from __future__ import annotations

from fastapi import APIRouter, Request


from ..errors import not_found
from ..models.session import (
    AbandonRequest,
    CompleteRequest,
    CompleteResponse,
    ProgressPatchRequest,
    ProgressResponse,
    SessionOut,
)
from .sessions import session_out

router = APIRouter()


@router.patch("/sessions/{session_id}/progress", response_model=ProgressResponse)
async def patch_progress(
    request: Request,
    session_id: str,
    payload: ProgressPatchRequest,
) -> ProgressResponse:
    store = request.app.state.store
    async with store.lock(store.session_rel(session_id)):
        session = await store.load_session(session_id)
        if not session:
            raise not_found("会话不存在。")
        progress = await request.app.state.progress_service.update_progress(session, payload)
    return ProgressResponse(
        progress=progress,
        session=session_out(session),
    )


@router.post("/sessions/{session_id}/pause", response_model=SessionOut)
async def pause_session(request: Request, session_id: str) -> SessionOut:
    store = request.app.state.store
    async with store.lock(store.session_rel(session_id)):
        session = await store.load_session(session_id)
        if not session:
            raise not_found("会话不存在。")
        session = await request.app.state.progress_service.pause(session)
    return session_out(session)


@router.post("/sessions/{session_id}/resume", response_model=SessionOut)
async def resume_session(request: Request, session_id: str) -> SessionOut:
    store = request.app.state.store
    async with store.lock(store.session_rel(session_id)):
        session = await store.load_session(session_id)
        if not session:
            raise not_found("会话不存在。")
        session = await request.app.state.progress_service.resume(session)
    return session_out(session)


@router.post("/sessions/{session_id}/complete", response_model=CompleteResponse)
async def complete_session(
    request: Request,
    session_id: str,
    payload: CompleteRequest,
) -> CompleteResponse:
    store = request.app.state.store
    async with store.lock(store.session_rel(session_id)):
        session = await store.load_session(session_id)
        if not session:
            raise not_found("会话不存在。")
        session, outcome = await request.app.state.progress_service.complete(session, payload)
    return CompleteResponse(session=session_out(session), outcome=outcome)


@router.post("/sessions/{session_id}/abandon", response_model=SessionOut)
async def abandon_session(
    request: Request,
    session_id: str,
    payload: AbandonRequest,
) -> SessionOut:
    store = request.app.state.store
    async with store.lock(store.session_rel(session_id)):
        session = await store.load_session(session_id)
        if not session:
            raise not_found("会话不存在。")
        session = await request.app.state.progress_service.abandon(session, payload.reason)
    return session_out(session)