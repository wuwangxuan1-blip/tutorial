from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from ..config import Settings
from ..enums import JobStatus, JobType, SessionStatus
from ..errors import ApiError, error_body
from ..ids import new_id
from ..models.feedback import FeedbackJobRequest
from .feedback_service import FeedbackService
from .media_service import MediaService
from .plan_service import PlanService
from .revision_service import RevisionService
from .store import JsonStore

logger = logging.getLogger("tutorial_coach.jobs")


def _now_dt() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def has_progress(session: dict[str, Any]) -> bool:
    progress = session.get("progress") or {}
    statuses = progress.get("step_statuses") or {}
    if progress.get("current_step_id") or progress.get("timer"):
        return True
    return any(
        status in ("in_progress", "done", "skipped") for status in statuses.values()
    )


class JobService:
    def __init__(
        self,
        settings: Settings,
        store: JsonStore,
        plan_service: PlanService,
        revision_service: RevisionService,
        feedback_service: FeedbackService,
        media_service: MediaService,
    ) -> None:
        self.settings = settings
        self.store = store
        self.plan_service = plan_service
        self.revision_service = revision_service
        self.feedback_service = feedback_service
        self.media_service = media_service
        self._tasks: dict[str, asyncio.Task[None]] = {}

    def active_count(self) -> int:
        return sum(1 for task in self._tasks.values() if not task.done())

    async def recover(self) -> None:
        jobs_dir = self.store.data_dir / "jobs"
        if not jobs_dir.exists():
            return
        for path in jobs_dir.glob("*.json"):
            try:
                job = await self.store.read_json(f"jobs/{path.name}")
            except ApiError:
                continue
            if not job or job.get("status") not in (JobStatus.queued.value, JobStatus.running.value):
                continue
            job["status"] = JobStatus.failed.value
            job["stage"] = "failed"
            job["updated_at"] = _iso(_now_dt())
            job["error"] = error_body(
                "SERVER_RESTARTED",
                "服务已重启，未完成的任务需重新创建。",
                new_id("request"),
                retryable=True,
            )
            await self.store.save_job(job)
            logger.warning(
                "job_failed_server_restarted",
                extra={"job_id": job["id"], "error_code": "SERVER_RESTARTED"},
            )

    async def create_plan_job(self, session: dict[str, Any], base_plan_version: int | None) -> dict[str, Any]:
        if self.active_count() >= self.settings.queue_max:
            raise ApiError(503, "JOB_QUEUE_FULL", "任务队列已满，请稍后重试。", retryable=True)
        now = _now_dt()
        job = {
            "id": new_id("job"),
            "type": JobType.plan_generation.value,
            "status": JobStatus.queued.value,
            "progress": 0,
            "stage": "queued",
            "session_id": session["id"],
            "created_at": _iso(now),
            "updated_at": _iso(now),
            "expires_at": _iso(now + timedelta(hours=24)),
            "result": None,
            "error": None,
            "_base_plan_version": base_plan_version,
        }
        await self.store.save_job(job)
        task = asyncio.create_task(self._run_plan_job(job["id"]))
        self._tasks[job["id"]] = task
        task.add_done_callback(lambda _: self._tasks.pop(job["id"], None))
        return job

    async def _set_job(self, job_id: str, **changes: Any) -> dict[str, Any]:
        job = await self.store.load_job(job_id)
        if not job:
            raise ApiError(404, "NOT_FOUND", "任务不存在。")
        job.update(changes)
        job["updated_at"] = _iso(_now_dt())
        await self.store.save_job(job)
        return job

    async def _run_plan_job(self, job_id: str) -> None:
        job = await self.store.load_job(job_id)
        if not job:
            return
        request_id = new_id("request")
        try:
            await self._set_job(job_id, status=JobStatus.running.value, progress=10, stage="analyzing")
            async with asyncio.timeout(self.settings.job_timeout_s):
                session = await self.store.load_session(job["session_id"])
                if not session:
                    raise ApiError(404, "NOT_FOUND", "会话不存在。")
                if session["domain"] not in ("cooking", "software", "photography", "coffee"):
                    raise ApiError(
                        422,
                        "DOMAIN_MISMATCH",
                        "本阶段仅启用烹饪、软件、摄影与咖啡领域的计划生成。",
                    )
                if session["status"] == SessionStatus.clarifying.value:
                    raise ApiError(422, "INVALID_REQUEST", "请先完成澄清问题。")
                if session["status"] in (
                    SessionStatus.completed.value,
                    SessionStatus.abandoned.value,
                ):
                    raise ApiError(409, "SESSION_NOT_EDITABLE", "会话已结束，不能生成计划。")
                if has_progress(session):
                    raise ApiError(
                        409,
                        "PLAN_LOCKED",
                        "已有步骤进度，不能全量重新生成；请使用条件修订或新建会话。",
                    )
                current_version = session.get("current_plan_version")
                base = job.get("_base_plan_version")
                if current_version is not None and base is None:
                    raise ApiError(
                        409,
                        "VERSION_CONFLICT",
                        "计划版本已变化，请刷新后重试。",
                        details={"current_plan_version": current_version},
                    )
                if current_version != base:
                    raise ApiError(
                        409,
                        "VERSION_CONFLICT",
                        "计划版本已变化，请刷新后重试。",
                        details={"current_plan_version": current_version},
                    )
                next_version = (current_version or 0) + 1
                plan = await self.plan_service.generate_plan(session, next_version)
                await self._set_job(job_id, progress=90, stage="validating")
                async with self.store.lock(self.store.session_rel(session["id"])):
                    fresh = await self.store.load_session(session["id"])
                    if not fresh:
                        raise ApiError(404, "NOT_FOUND", "会话不存在。")
                    if fresh["status"] in (
                        SessionStatus.completed.value,
                        SessionStatus.abandoned.value,
                    ):
                        raise ApiError(409, "SESSION_NOT_EDITABLE", "会话已结束，不能生成计划。")
                    if has_progress(fresh):
                        raise ApiError(
                            409,
                            "PLAN_LOCKED",
                            "生成期间出现了步骤进度，已取消本次写入。",
                        )
                    if fresh.get("current_plan_version") != base:
                        raise ApiError(
                            409,
                            "VERSION_CONFLICT",
                            "计划版本已变化，未写入本次结果。",
                            details={"current_plan_version": fresh.get("current_plan_version")},
                        )
                    await self.store.save_plan(plan)
                    fresh["current_plan_version"] = next_version
                    fresh["updated_at"] = _iso(_now_dt())
                    await self.store.save_session(fresh)
            await self._set_job(
                job_id,
                status=JobStatus.succeeded.value,
                progress=100,
                stage="done",
                result={"plan_id": plan["id"], "plan_version": next_version},
                error=None,
            )
            logger.info(
                "job_succeeded",
                extra={"job_id": job_id, "session_id": session["id"], "status": "succeeded"},
            )
        except asyncio.TimeoutError:
            await self._fail(
                job_id,
                request_id,
                ApiError(504, "MODEL_TIMEOUT", "生成计划超时，请重试。", retryable=True),
            )
        except ApiError as exc:
            await self._fail(job_id, request_id, exc)
        except Exception:
            logger.exception("job_unexpected_error", extra={"job_id": job_id, "error_code": "INTERNAL_ERROR"})
            await self._fail(
                job_id,
                request_id,
                ApiError(500, "INTERNAL_ERROR", "生成计划时发生内部错误。", retryable=True),
            )

    async def create_feedback_job(
        self,
        session: dict[str, Any],
        payload: FeedbackJobRequest,
    ) -> dict[str, Any]:
        if self.active_count() >= self.settings.queue_max:
            raise ApiError(503, "JOB_QUEUE_FULL", "任务队列已满，请稍后重试。", retryable=True)
        now = _now_dt()
        job = {
            "id": new_id("job"),
            "type": JobType.feedback_analysis.value,
            "status": JobStatus.queued.value,
            "progress": 0,
            "stage": "queued",
            "session_id": session["id"],
            "created_at": _iso(now),
            "updated_at": _iso(now),
            "expires_at": _iso(now + timedelta(hours=24)),
            "result": None,
            "error": None,
            "_step_id": payload.step_id,
            "_plan_version": payload.plan_version,
            "_media_ids": list(payload.media_ids),
            "_note": payload.note,
        }
        await self.store.save_job(job)
        progress = dict(session.get("progress") or {})
        evidence_levels = dict(progress.get("evidence_levels") or {})
        if evidence_levels.get(payload.step_id) != "measured":
            evidence_levels[payload.step_id] = "media_submitted"
        progress["evidence_levels"] = evidence_levels
        progress["updated_at"] = _iso(now)
        session["progress"] = progress
        session["updated_at"] = _iso(now)
        await self.store.save_session(session)
        task = asyncio.create_task(self._run_feedback_job(job["id"]))
        self._tasks[job["id"]] = task
        task.add_done_callback(lambda _: self._tasks.pop(job["id"], None))
        return job

    async def _run_feedback_job(self, job_id: str) -> None:
        job = await self.store.load_job(job_id)
        if not job:
            return
        request_id = new_id("request")
        try:
            await self._set_job(
                job_id,
                status=JobStatus.running.value,
                progress=10,
                stage="validating_media",
            )
            async with asyncio.timeout(self.settings.job_timeout_s):
                session = await self.store.load_session(job["session_id"])
                if not session:
                    raise ApiError(404, "NOT_FOUND", "会话不存在。")
                version = job.get("_plan_version")
                if session.get("current_plan_version") != version:
                    raise ApiError(
                        409,
                        "VERSION_CONFLICT",
                        "计划版本已变化，请刷新后重试。",
                        details={"current_plan_version": session.get("current_plan_version")},
                    )
                plan = await self.store.load_plan(session["id"], version)
                if not plan:
                    raise ApiError(404, "NOT_FOUND", "当前计划不存在。")
                step = next(
                    (item for item in plan["steps"] if item["id"] == job.get("_step_id")),
                    None,
                )
                if not step:
                    raise ApiError(422, "INVALID_REQUEST", "步骤不属于当前计划。")
                payload = FeedbackJobRequest(
                    step_id=job["_step_id"],
                    plan_version=version,
                    media_ids=job.get("_media_ids") or [],
                    note=job.get("_note") or "",
                )
                media_items = await self.feedback_service.validate_request(session, plan, payload)
                await self._set_job(job_id, progress=50, stage="analyzing_media")
                feedback = await self.feedback_service.analyze(
                    session,
                    plan,
                    step,
                    media_items,
                    payload.note,
                )
            await self._set_job(
                job_id,
                status=JobStatus.succeeded.value,
                progress=100,
                stage="done",
                result={"feedback_id": feedback["id"]},
                error=None,
            )
            logger.info(
                "feedback_job_succeeded",
                extra={"job_id": job_id, "session_id": session["id"], "status": "succeeded"},
            )
        except asyncio.TimeoutError:
            await self._fail(
                job_id,
                request_id,
                ApiError(504, "MODEL_TIMEOUT", "媒体反馈分析超时，请重试。", retryable=True),
            )
        except ApiError as exc:
            await self._fail(job_id, request_id, exc)
        except Exception:
            logger.exception(
                "feedback_job_unexpected_error",
                extra={"job_id": job_id, "error_code": "INTERNAL_ERROR"},
            )
            await self._fail(
                job_id,
                request_id,
                ApiError(500, "INTERNAL_ERROR", "分析媒体时发生内部错误。", retryable=True),
            )

    async def create_revision_job(
        self,
        session: dict[str, Any],
        base_plan_version: int,
        request_reason: str,
    ) -> dict[str, Any]:
        if self.active_count() >= self.settings.queue_max:
            raise ApiError(503, "JOB_QUEUE_FULL", "任务队列已满，请稍后重试。", retryable=True)
        now = _now_dt()
        job = {
            "id": new_id("job"),
            "type": JobType.plan_revision.value,
            "status": JobStatus.queued.value,
            "progress": 0,
            "stage": "queued",
            "session_id": session["id"],
            "created_at": _iso(now),
            "updated_at": _iso(now),
            "expires_at": _iso(now + timedelta(hours=24)),
            "result": None,
            "error": None,
            "_base_plan_version": base_plan_version,
            "_request_reason": request_reason,
        }
        await self.store.save_job(job)
        task = asyncio.create_task(self._run_revision_job(job["id"]))
        self._tasks[job["id"]] = task
        task.add_done_callback(lambda _: self._tasks.pop(job["id"], None))
        return job

    async def _run_revision_job(self, job_id: str) -> None:
        job = await self.store.load_job(job_id)
        if not job:
            return
        request_id = new_id("request")
        try:
            await self._set_job(
                job_id,
                status=JobStatus.running.value,
                progress=10,
                stage="analyzing",
            )
            async with asyncio.timeout(self.settings.job_timeout_s):
                session = await self.store.load_session(job["session_id"])
                if not session:
                    raise ApiError(404, "NOT_FOUND", "会话不存在。")
                if session["status"] in (
                    SessionStatus.completed.value,
                    SessionStatus.abandoned.value,
                ):
                    raise ApiError(409, "SESSION_NOT_EDITABLE", "会话已结束，不能生成修订。")
                base = job.get("_base_plan_version")
                if session.get("current_plan_version") != base:
                    raise ApiError(
                        409,
                        "VERSION_CONFLICT",
                        "计划版本已变化，请刷新后重试。",
                        details={"current_plan_version": session.get("current_plan_version")},
                    )
                plan = await self.store.load_plan(session["id"], base)
                if not plan:
                    raise ApiError(404, "NOT_FOUND", "当前计划不存在。")
                await self._set_job(job_id, progress=60, stage="validating")
                revision = await self.revision_service.generate(
                    session,
                    plan,
                    job.get("_request_reason") or "根据条件调整未完成步骤。",
                )
            if revision is None:
                await self._set_job(
                    job_id,
                    status=JobStatus.succeeded.value,
                    progress=100,
                    stage="no_change",
                    result={"revision_id": None},
                    error=None,
                )
            else:
                await self._set_job(
                    job_id,
                    status=JobStatus.succeeded.value,
                    progress=100,
                    stage="done",
                    result={"revision_id": revision["id"]},
                    error=None,
                )
            logger.info(
                "revision_job_succeeded",
                extra={"job_id": job_id, "session_id": session["id"], "status": "succeeded"},
            )
        except asyncio.TimeoutError:
            await self._fail(
                job_id,
                request_id,
                ApiError(504, "MODEL_TIMEOUT", "生成修订超时，请重试。", retryable=True),
            )
        except ApiError as exc:
            await self._fail(job_id, request_id, exc)
        except Exception:
            logger.exception(
                "revision_job_unexpected_error",
                extra={"job_id": job_id, "error_code": "INTERNAL_ERROR"},
            )
            await self._fail(
                job_id,
                request_id,
                ApiError(500, "INTERNAL_ERROR", "生成修订时发生内部错误。", retryable=True),
            )

    async def _fail(self, job_id: str, request_id: str, exc: ApiError) -> None:
        await self._set_job(
            job_id,
            status=JobStatus.failed.value,
            progress=100,
            stage="failed",
            error=error_body(
                exc.code,
                exc.message,
                request_id,
                retryable=exc.retryable,
                retry_after_s=exc.retry_after_s,
                details=exc.details,
            ),
            result=None,
        )
        logger.warning(
            "job_failed",
            extra={"job_id": job_id, "error_code": exc.code, "status": "failed"},
        )

    async def get_job(self, job_id: str) -> dict[str, Any]:
        job = await self.store.load_job(job_id)
        if not job:
            raise ApiError(404, "NOT_FOUND", "任务不存在。")
        terminal = job["status"] in (
            JobStatus.succeeded.value,
            JobStatus.failed.value,
            JobStatus.cancelled.value,
        )
        if terminal and _parse_iso(job["expires_at"]) < _now_dt():
            raise ApiError(410, "JOB_EXPIRED", "任务结果已过期，请重新创建。")
        return job

    async def cancel(self, job_id: str) -> dict[str, Any]:
        job = await self.get_job(job_id)
        if job["status"] not in (JobStatus.queued.value, JobStatus.running.value):
            raise ApiError(409, "JOB_NOT_CANCELLABLE", "任务已结束，不能取消。")
        task = self._tasks.get(job_id)
        if task:
            task.cancel()
        job["status"] = JobStatus.cancelled.value
        job["stage"] = "cancelled"
        job["updated_at"] = _iso(_now_dt())
        await self.store.save_job(job)
        return job