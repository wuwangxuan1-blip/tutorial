from __future__ import annotations

from fastapi import APIRouter, Request

from ..errors import not_found
from ..models.session import AskRequest, AskResponse

router = APIRouter()


@router.post("/sessions/{session_id}/ask", response_model=AskResponse)
async def ask(request: Request, session_id: str, payload: AskRequest) -> AskResponse:
    store = request.app.state.store
    session = await store.load_session(session_id)
    if not session:
        raise not_found("会话不存在。")
    result = await request.app.state.ask_service.ask(session, payload)
    return AskResponse.model_validate(result)