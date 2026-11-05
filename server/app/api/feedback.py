from __future__ import annotations

from fastapi import APIRouter, Query, Request

from ..errors import ApiError, not_found
from ..models.feedback import FeedbackJobRequest, FeedbackListResponse, FeedbackOut
from ..models.job import JobOut
from .sessions import job_out

router = APIRouter()


@router.post(
    "/sessions/{session_id}/feedback-jobs",
    response_model=JobOut,
    status_code=202,
)
async def create_feedback_job(
    request: Request,
    session_id: str,
    payload: FeedbackJobRequest,
) -> JobOut:
    store = request.app.state.store
    async with store.lock(store.session_rel(session_id)):
        session = await store.load_session(session_id)
        if not session:
            raise not_found("会话不存在。")
        version = session.get("current_plan_version")
        if version is None:
            raise not_found("当前计划不存在。")
        if payload.plan_version != version:
            raise ApiError(
                409,
                "VERSION_CONFLICT",
                "计划版本已变化，请刷新后重试。",
                details={"current_plan_version": version},
            )
        plan = await store.load_plan(session_id, version)
        if not plan:
            raise not_found("当前计划不存在。")
        await request.app.state.feedback_service.validate_request(session, plan, payload)
        job = await request.app.state.job_service.create_feedback_job(session, payload)
    return job_out(job)


@router.get("/sessions/{session_id}/feedback", response_model=FeedbackListResponse)
async def list_feedback(
    request: Request,
    session_id: str,
    step_id: str | None = Query(default=None),
) -> FeedbackListResponse:
    store = request.app.state.store
    session = await store.load_session(session_id)
    if not session:
        raise not_found("会话不存在。")
    items = await request.app.state.feedback_service.list_for_session(session_id, step_id)
    return FeedbackListResponse(items=[FeedbackOut.model_validate(item) for item in items])


@router.get("/feedback/{feedback_id}", response_model=FeedbackOut)
async def get_feedback(request: Request, feedback_id: str) -> FeedbackOut:
    result = await request.app.state.feedback_service.get(feedback_id)
    return FeedbackOut.model_validate(result)