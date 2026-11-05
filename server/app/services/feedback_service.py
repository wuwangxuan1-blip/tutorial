from __future__ import annotations

import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from ..config import Settings
from ..enums import SessionStatus
from ..errors import ApiError, invalid_request, not_found
from ..ids import new_id
from ..models.feedback import (
    FeedbackAnalysis,
    FeedbackDraft,
    FeedbackJobRequest,
    FeedbackOut,
    MotionMetrics,
)
from .ffmpeg import FFmpegError, extract_frames, motion_metrics
from .media_service import MediaService
from .model_client import ModelClient
from .prompt_builder import build_feedback_user_prompt, load_prompt
from .store import JsonStore


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _append_unique(items: list[str], additions: list[str], limit: int) -> list[str]:
    result = list(items)
    for item in additions:
        if item not in result and len(result) < limit:
            result.append(item)
    return result


class FeedbackService:
    def __init__(
        self,
        settings: Settings,
        model_client: ModelClient,
        store: JsonStore,
        media_service: MediaService,
    ) -> None:
        self.settings = settings
        self.model_client = model_client
        self.store = store
        self.media_service = media_service

    async def validate_request(
        self,
        session: dict[str, Any],
        plan: dict[str, Any],
        payload: FeedbackJobRequest,
    ) -> list[dict[str, Any]]:
        if session["status"] in (
            SessionStatus.completed.value,
            SessionStatus.abandoned.value,
        ):
            raise ApiError(409, "SESSION_NOT_EDITABLE", "会话已结束，不能提交反馈。")
        current_version = session.get("current_plan_version")
        if current_version is None:
            raise not_found("该会话还没有计划，不能提交反馈。")
        if payload.plan_version != current_version:
            raise ApiError(
                409,
                "VERSION_CONFLICT",
                "计划版本已变化，请刷新后重试。",
                details={"current_plan_version": current_version},
            )
        if payload.step_id not in {step["id"] for step in plan["steps"]}:
            raise invalid_request(
                "步骤不属于当前计划。",
                {"field": "step_id", "reason": "unknown_step"},
            )
        if len(payload.media_ids) != len(set(payload.media_ids)):
            raise invalid_request("media_ids 不能重复。", {"field": "media_ids"})
        media_items: list[dict[str, Any]] = []
        for media_id in payload.media_ids:
            data = await self.store.load_media(media_id)
            if not data:
                raise not_found("媒体不存在或已删除。")
            if data.get("status") != "ready":
                raise invalid_request("媒体尚未就绪。", {"field": "media_ids"})
            media_items.append(data)
        kinds = {item["kind"] for item in media_items}
        if len(kinds) != 1:
            raise invalid_request(
                "一次反馈不能混用图片和视频。",
                {"field": "media_ids", "reason": "mixed_media"},
            )
        if "image" in kinds:
            if not 1 <= len(media_items) <= 4:
                raise invalid_request("图片反馈需要 1–4 张图片。", {"field": "media_ids"})
        else:
            if len(media_items) != 1:
                raise invalid_request("视频反馈每次只能提交 1 段视频。", {"field": "media_ids"})
        return media_items

    async def analyze(
        self,
        session: dict[str, Any],
        plan: dict[str, Any],
        step: dict[str, Any],
        media_items: list[dict[str, Any]],
        note: str,
    ) -> dict[str, Any]:
        if not self.settings.vision_model:
            raise ApiError(
                503,
                "VISION_UNSUPPORTED",
                "当前服务端未配置视觉模型，不能生成媒体反馈。",
            )
        kind = media_items[0]["kind"]
        images: list[tuple[bytes, str]] = []
        frames: list[tuple[int, float]] = []
        frame_images: list[tuple[int, bytes]] = []
        metrics: dict[str, Any] | None = None
        with tempfile.TemporaryDirectory(prefix="tutorial_feedback_") as temporary:
            temp_dir = Path(temporary)
            if kind == "image":
                for item in media_items:
                    images.append((self.media_service.file_path(item).read_bytes(), "image/jpeg"))
            else:
                video = media_items[0]
                path = self.media_service.file_path(video)
                try:
                    extracted = await extract_frames(
                        path,
                        int(video["width"]),
                        int(video["height"]),
                        float(video.get("duration_s") or 0),
                        temp_dir,
                    )
                except FFmpegError as exc:
                    raise ApiError(
                        422,
                        "MEDIA_DECODE_FAILED",
                        "视频抽帧失败，请转为 H.264 MP4 后重试。",
                    ) from exc
                frames = [(frame.index, frame.timestamp_s) for frame in extracted]
                frame_images = [
                    (frame.index, frame.path.read_bytes())
                    for frame in extracted
                ]
                images = [(data, "image/jpeg") for _, data in frame_images]
                try:
                    metrics = await motion_metrics(path, temp_dir)
                except FFmpegError:
                    metrics = None

            user_prompt = build_feedback_user_prompt(
                session["goal"],
                session["domain"],
                step,
                media_items,
                frames,
                metrics,
                note,
            )
            system_prompt = load_prompt("feedback")
            raw = await self.model_client.chat_json(
                system_prompt,
                user_prompt,
                model=self.settings.vision_model,
                timeout_s=90,
                vision_images=images,
            )

        try:
            draft = FeedbackDraft.model_validate(raw)
        except ValidationError as exc:
            raise ApiError(
                502,
                "MODEL_BAD_OUTPUT",
                "模型返回的反馈格式异常，请重试。",
                retryable=True,
                details={"reason": "feedback_validation_failed"},
            ) from exc

        media_by_id = {item["id"]: item for item in media_items}
        frame_map = {index: timestamp for index, timestamp in frames}
        for observation in draft.observations:
            evidence = observation.evidence
            if evidence.media_id not in media_by_id:
                raise ApiError(
                    502,
                    "MODEL_BAD_OUTPUT",
                    "模型引用了本次未提交的媒体。",
                    retryable=True,
                    details={"reason": "evidence_media_mismatch"},
                )
            media = media_by_id[evidence.media_id]
            if media["kind"] == "image":
                if evidence.kind != "image":
                    raise ApiError(
                        502,
                        "MODEL_BAD_OUTPUT",
                        "图片反馈的证据类型不一致。",
                        retryable=True,
                        details={"reason": "evidence_kind_mismatch"},
                    )
            else:
                if evidence.kind != "video_frame" or evidence.frame_index is None:
                    raise ApiError(
                        502,
                        "MODEL_BAD_OUTPUT",
                        "视频反馈的证据必须引用实际抽帧。",
                        retryable=True,
                        details={"reason": "evidence_kind_mismatch"},
                    )
                timestamp = frame_map.get(evidence.frame_index)
                if timestamp is None or evidence.timestamp_s is None:
                    raise ApiError(
                        502,
                        "MODEL_BAD_OUTPUT",
                        "模型引用了不存在的视频帧。",
                        retryable=True,
                        details={"reason": "evidence_frame_mismatch"},
                    )
                if abs(timestamp - evidence.timestamp_s) > 0.02:
                    raise ApiError(
                        502,
                        "MODEL_BAD_OUTPUT",
                        "模型引用的时间戳与实际抽帧不一致。",
                        retryable=True,
                        details={"reason": "evidence_timestamp_mismatch"},
                    )

        domain_limitations = {
            "cooking": [
                "照片无法判断食物内部温度与食用安全。",
                "无法判断实际口味。",
            ],
            "photography": [
                "单帧/短片只能做定性观察，不提供精确稳定性评分。",
                "2D 画面不代表真实焦距、景深或精确轨迹。",
            ],
            "software": ["截图不能代替实际系统状态验证。"],
            "coffee": ["照片不能推断咖啡口味或萃取参数。"],
        }.get(session["domain"], [])
        limitations = _append_unique(draft.limitations, domain_limitations, 5)
        if kind == "video" and metrics is None:
            limitations = _append_unique(limitations, ["未启用运动估计（vidstabdetect 失败或不可用）。"], 5)
        limitations = _append_unique(limitations, ["本期不分析音频，也不生成转写。"], 5)
        uncertainties = list(draft.uncertainties)
        assessment = draft.assessment
        if not draft.observations:
            assessment = "unclear"
            uncertainties = _append_unique(
                uncertainties,
                ["模型没有给出可引用本次媒体的观察，未形成结论。"],
                5,
            )
        if assessment in ("unclear", "not_verified") and not uncertainties:
            uncertainties = ["证据不足，无法形成确定结论。"]

        motion: MotionMetrics | None = None
        if kind == "video" and metrics is not None:
            motion = MotionMetrics.model_validate(metrics)
        analysis = FeedbackAnalysis(
            summary=draft.summary,
            observations=draft.observations,
            assessment=assessment,
            uncertainties=uncertainties,
            limitations=limitations,
            motion_metrics=motion,
            sampled_frame_timestamps_s=[timestamp for _, timestamp in frames],
            audio_analyzed=False,
            audio_note="本期不分析音频，也不生成转写。",
        )
        feedback = {
            "id": new_id("feedback"),
            "session_id": session["id"],
            "step_id": step["id"],
            "plan_version": plan["version"],
            "media_ids": [item["id"] for item in media_items],
            "analysis": analysis.model_dump(mode="json"),
            "suggested_actions": draft.suggested_actions,
            "follow_up_questions": draft.follow_up_questions,
            "revision_id": None,
            "created_at": _now(),
        }
        await self._persist_feedback(
            feedback,
            plan_version=plan["version"],
            step_id=step["id"],
            mark_observed=bool(analysis.observations),
            evidence_frames=frame_images,
        )
        return feedback

    async def _persist_feedback(
        self,
        feedback: dict[str, Any],
        *,
        plan_version: int,
        step_id: str,
        mark_observed: bool,
        evidence_frames: list[tuple[int, bytes]] | None = None,
    ) -> None:
        session_id = feedback["session_id"]
        async with self.store.lock(self.store.session_rel(session_id)):
            fresh = await self.store.load_session(session_id)
            if not fresh:
                raise not_found("会话不存在。")
            if fresh["status"] in (
                SessionStatus.completed.value,
                SessionStatus.abandoned.value,
            ):
                raise ApiError(409, "SESSION_NOT_EDITABLE", "会话已结束，不能写入反馈。")
            current_version = fresh.get("current_plan_version")
            if current_version != plan_version:
                raise ApiError(
                    409,
                    "VERSION_CONFLICT",
                    "计划版本已变化，反馈结果未写入，请刷新后重试。",
                    details={"current_plan_version": current_version},
                )
            current_plan = await self.store.load_plan(session_id, plan_version)
            if not current_plan or step_id not in {
                step["id"] for step in current_plan["steps"]
            }:
                raise invalid_request(
                    "步骤不属于当前计划。",
                    {"field": "step_id", "reason": "unknown_step"},
                )
            if mark_observed:
                progress = dict(fresh.get("progress") or {})
                evidence_levels = dict(progress.get("evidence_levels") or {})
                if evidence_levels.get(step_id) != "measured":
                    evidence_levels[step_id] = "model_observed"
                progress["evidence_levels"] = evidence_levels
                progress["updated_at"] = _now()
                fresh["progress"] = progress
                fresh["updated_at"] = _now()
            if evidence_frames:
                await self.store.save_feedback_frames(feedback["id"], evidence_frames)
            await self.store.save_feedback(feedback)
            if mark_observed:
                await self.store.save_session(fresh)

    async def get(self, feedback_id: str) -> dict[str, Any]:
        feedback = await self.store.load_feedback(feedback_id)
        if not feedback:
            raise not_found("反馈不存在。")
        return FeedbackOut.model_validate(feedback).model_dump(mode="json")

    async def list_for_session(
        self,
        session_id: str,
        step_id: str | None = None,
    ) -> list[dict[str, Any]]:
        items = await self.store.list_feedback(session_id)
        if step_id:
            items = [item for item in items if item.get("step_id") == step_id]
        return [FeedbackOut.model_validate(item).model_dump(mode="json") for item in items]