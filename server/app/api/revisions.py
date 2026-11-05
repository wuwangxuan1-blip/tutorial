from __future__ import annotations

from fastapi import APIRouter, Request

from ..errors import ApiError, invalid_request, not_found
from ..models.job import JobOut
from ..models.revision import (
    RevisionApplyRequest,
    RevisionApplyResponse,
    RevisionJobRequest,
    RevisionOut,
    RevisionRejectRequest,
)
from .sessions import job_out

router = APIRouter()


@router.get("/sessions/{session_id}/revisions", response_model=list[RevisionOut])
async def list_revisions(request: Request, session_id: str) -> list[RevisionOut]:
    store = request.app.state.store
    session = await store.load_session(session_id)
    if not session:
        raise not_found("会话不存在。")
    items = await store.list_revisions(session_id)
    return [RevisionOut.model_validate(item) for item in items]


@router.post("/sessions/{session_id}/revision-jobs", response_model=JobOut, status_code=202)
async def create_revision_job(
    request: Request,
    session_id: str,
    payload: RevisionJobRequest,
) -> JobOut:
    store = request.app.state.store
    async with store.lock(store.session_rel(session_id)):
        session = await store.load_session(session_id)
        if not session:
            raise not_found("会话不存在。")
        if session["status"] in ("completed", "abandoned"):
            raise ApiError(409, "SESSION_NOT_EDITABLE", "会话已结束，不能生成修订。")
        version = session.get("current_plan_version")
        if version is None:
            raise invalid_request("该会话还没有计划，不能生成修订。")
        if payload.base_plan_version != version:
            raise ApiError(
                409,
                "VERSION_CONFLICT",
                "计划版本已变化，请刷新后重试。",
                details={"current_plan_version": version},
            )
        if payload.feedback_id is not None:
            raise invalid_request(
                "本阶段尚未启用媒体反馈驱动修订；请使用条件修订。",
                {"field": "feedback_id", "reason": "feedback_not_available"},
            )
        if not payload.request_reason:
            raise invalid_request(
                "条件修订必须提供 request_reason。",
                {"field": "request_reason", "reason": "missing_request_reason"},
            )
        job = await request.app.state.job_service.create_revision_job(
            session,
            version,
            payload.request_reason,
        )
    return job_out(job)


@router.post(
    "/sessions/{session_id}/revisions/{revision_id}/apply",
    response_model=RevisionApplyResponse,
)
async def apply_revision(
    request: Request,
    session_id: str,
    revision_id: str,
    payload: RevisionApplyRequest,
) -> RevisionApplyResponse:
    store = request.app.state.store
    async with store.lock(store.session_rel(session_id)):
        session = await store.load_session(session_id)
        if not session:
            raise not_found("会话不存在。")
        revision = await store.load_revision(session_id, revision_id)
        if not revision:
            raise not_found("修订不存在。")
        plan, revision = await request.app.state.revision_service.apply(
            session,
            revision,
            payload.base_plan_version,
        )
    return RevisionApplyResponse(
        plan=plan,
        revision=RevisionOut.model_validate(revision),
    )


@router.post(
    "/sessions/{session_id}/revisions/{revision_id}/reject",
    response_model=RevisionOut,
)
async def reject_revision(
    request: Request,
    session_id: str,
    revision_id: str,
    payload: RevisionRejectRequest,
) -> RevisionOut:
    store = request.app.state.store
    async with store.lock(store.session_rel(session_id)):
        session = await store.load_session(session_id)
        if not session:
            raise not_found("会话不存在。")
        revision = await store.load_revision(session_id, revision_id)
        if not revision:
            raise not_found("修订不存在。")
        revision = await request.app.state.revision_service.reject(
            revision,
            payload.reason,
        )
    return RevisionOut.model_validate(revision)