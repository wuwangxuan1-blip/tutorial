from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..enums import EvidenceLevel, SessionStatus, StepStatus
from ..errors import ApiError, invalid_request, not_found
from ..models.session import CompleteRequest, ProgressPatchRequest, Progress
from .store import JsonStore

TERMINAL_STATUSES = (SessionStatus.completed.value, SessionStatus.abandoned.value)
ALLOWED_STEP_TRANSITIONS: dict[str, set[str]] = {
    StepStatus.not_started.value: {
        StepStatus.not_started.value,
        StepStatus.in_progress.value,
        StepStatus.done.value,
        StepStatus.skipped.value,
    },
    StepStatus.in_progress.value: {
        StepStatus.in_progress.value,
        StepStatus.done.value,
        StepStatus.skipped.value,
    },
    StepStatus.done.value: {StepStatus.done.value},
    StepStatus.skipped.value: {StepStatus.skipped.value},
}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class ProgressService:
    def __init__(self, store: JsonStore) -> None:
        self.store = store

    async def update_progress(
        self,
        session: dict[str, Any],
        payload: ProgressPatchRequest,
    ) -> dict[str, Any]:
        status = session["status"]
        if status == SessionStatus.paused.value:
            raise ApiError(409, "SESSION_PAUSED", "会话已暂停，不能写入进度；请先恢复。")
        if status in TERMINAL_STATUSES:
            raise ApiError(409, "SESSION_NOT_EDITABLE", "会话已结束，不能写入进度。")
        if status not in (SessionStatus.ready.value, SessionStatus.in_progress.value):
            raise invalid_request("当前会话不能写入进度。", {"reason": "session_not_started"})

        version = session.get("current_plan_version")
        if version is None:
            raise not_found("该会话还没有计划，不能写入进度。")
        if payload.base_plan_version != version:
            raise ApiError(
                409,
                "VERSION_CONFLICT",
                "计划版本已变化，请刷新后重试。",
                details={"current_plan_version": version},
            )
        plan = await self.store.load_plan(session["id"], version)
        if not plan:
            raise not_found("该会话还没有计划，不能写入进度。")
        step_ids = {step["id"] for step in plan["steps"]}

        progress = dict(session.get("progress") or {})
        statuses = dict(progress.get("step_statuses") or {})
        evidences = dict(progress.get("evidence_levels") or {})

        if payload.step_statuses is not None:
            for step_id, new_status in payload.step_statuses.items():
                if step_id not in step_ids:
                    raise invalid_request(
                        "步骤不属于当前计划。",
                        {"field": step_id, "reason": "unknown_step"},
                    )
                old_status = statuses.get(step_id, StepStatus.not_started.value)
                if new_status.value not in ALLOWED_STEP_TRANSITIONS.get(old_status, set()):
                    raise invalid_request(
                        "不允许的步骤状态变更。",
                        {
                            "field": step_id,
                            "reason": "step_status_locked",
                            "from": old_status,
                            "to": new_status.value,
                        },
                    )
                statuses[step_id] = new_status.value
                if new_status == StepStatus.done:
                    evidences.setdefault(step_id, EvidenceLevel.self_reported.value)
                elif new_status == StepStatus.skipped:
                    evidences.setdefault(step_id, EvidenceLevel.none.value)

        if payload.evidence_levels is not None:
            for step_id, level in payload.evidence_levels.items():
                if step_id not in step_ids:
                    raise invalid_request(
                        "证据等级对应的步骤不属于当前计划。",
                        {"field": step_id, "reason": "unknown_step"},
                    )
                evidences[step_id] = level.value

        if "current_step_id" in payload.model_fields_set:
            current = payload.current_step_id
            if current is not None and current not in step_ids:
                raise invalid_request(
                    "当前步骤不属于当前计划。",
                    {"field": "current_step_id", "reason": "unknown_step"},
                )
            progress["current_step_id"] = current

        if "timer" in payload.model_fields_set:
            timer = payload.timer
            if timer is None:
                progress["timer"] = None
            else:
                if timer.step_id not in step_ids:
                    raise invalid_request(
                        "计时器步骤不属于当前计划。",
                        {"field": "timer.step_id", "reason": "unknown_step"},
                    )
                current_step = progress.get("current_step_id")
                if current_step is not None and timer.step_id != current_step:
                    raise invalid_request(
                        "计时器步骤必须与当前步骤一致。",
                        {"field": "timer.step_id", "reason": "timer_step_mismatch"},
                    )
                progress["timer"] = timer.model_dump(mode="json")

        for step_id, step_status in statuses.items():
            if step_status == StepStatus.done.value and evidences.get(step_id) in (
                None,
                EvidenceLevel.none.value,
            ):
                evidences[step_id] = EvidenceLevel.self_reported.value

        now = _now()
        progress["step_statuses"] = statuses
        progress["evidence_levels"] = evidences
        progress["updated_at"] = now
        Progress.model_validate(progress)
        session["progress"] = progress
        if session["status"] == SessionStatus.ready.value:
            session["status"] = SessionStatus.in_progress.value
        session["updated_at"] = now
        await self.store.save_session(session)
        return progress

    async def pause(self, session: dict[str, Any]) -> dict[str, Any]:
        if session["status"] != SessionStatus.in_progress.value:
            raise invalid_request(
                "只有进行中的会话可以暂停。",
                {"reason": "session_not_in_progress"},
            )
        session["status"] = SessionStatus.paused.value
        session["updated_at"] = _now()
        await self.store.save_session(session)
        return session

    async def resume(self, session: dict[str, Any]) -> dict[str, Any]:
        if session["status"] != SessionStatus.paused.value:
            raise invalid_request(
                "只有暂停中的会话可以恢复。",
                {"reason": "session_not_paused"},
            )
        session["status"] = SessionStatus.in_progress.value
        session["updated_at"] = _now()
        await self.store.save_session(session)
        return session

    async def complete(
        self,
        session: dict[str, Any],
        payload: CompleteRequest,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        if session["status"] not in (
            SessionStatus.in_progress.value,
            SessionStatus.paused.value,
        ):
            raise ApiError(409, "SESSION_NOT_EDITABLE", "当前会话不能标记完成。")
        if payload.photo_media_ids:
            raise invalid_request(
                "本阶段尚未启用媒体照片；照片记录将在后续阶段开放。",
                {"field": "photo_media_ids", "reason": "media_not_available"},
            )
        now = _now()
        outcome = {
            "rating": payload.rating,
            "notes": payload.notes,
            "photo_media_ids": [],
            "verification": "user_reported",
            "completed_at": now,
        }
        session["status"] = SessionStatus.completed.value
        session["outcome"] = outcome
        session["updated_at"] = now
        await self.store.save_session(session)
        return session, outcome

    async def abandon(self, session: dict[str, Any], reason: str) -> dict[str, Any]:
        if session["status"] in TERMINAL_STATUSES:
            raise ApiError(409, "SESSION_NOT_EDITABLE", "会话已结束。")
        session["status"] = SessionStatus.abandoned.value
        session["outcome"] = {"reason": reason, "verification": "user_reported"}
        session["updated_at"] = _now()
        await self.store.save_session(session)
        return session