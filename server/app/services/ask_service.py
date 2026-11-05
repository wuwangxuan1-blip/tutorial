from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from ..config import Settings
from ..errors import ApiError, invalid_request, not_found
from ..ids import new_id
from ..models.session import AskRequest
from .model_client import ModelClient
from .prompt_builder import build_ask_user_prompt, load_prompt
from .store import JsonStore


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class AskService:
    def __init__(
        self,
        settings: Settings,
        model_client: ModelClient,
        store: JsonStore,
    ) -> None:
        self.settings = settings
        self.model_client = model_client
        self.store = store

    async def ask(self, session: dict[str, Any], payload: AskRequest) -> dict[str, Any]:
        version = session.get("current_plan_version")
        if version is None:
            raise not_found("该会话还没有计划，不能提问。")
        if payload.plan_version is not None and payload.plan_version != version:
            raise ApiError(
                409,
                "VERSION_CONFLICT",
                "计划版本已变化，请刷新后重试。",
                details={"current_plan_version": version},
            )
        plan = await self.store.load_plan(session["id"], version)
        if not plan:
            raise not_found("该会话还没有计划，不能提问。")
        step_map = {step["id"]: step for step in plan["steps"]}
        step_id = payload.step_id or (session.get("progress") or {}).get("current_step_id")
        if not step_id or step_id not in step_map:
            raise invalid_request(
                "请提供当前计划中的步骤。",
                {"field": "step_id", "reason": "unknown_step"},
            )
        system_prompt = load_prompt("ask")
        user_prompt = build_ask_user_prompt(
            session["goal"],
            session["domain"],
            step_map[step_id],
            payload.question,
        )
        try:
            async with asyncio.timeout(60):
                raw = await self.model_client.chat_json(
                    system_prompt,
                    user_prompt,
                    timeout_s=45,
                )
        except TimeoutError as exc:
            raise ApiError(
                504,
                "MODEL_TIMEOUT",
                "提问超时，请重试；本次未返回答案。",
                retryable=True,
            ) from exc

        answer = raw.get("answer")
        citations = raw.get("citations", [])
        limitations = raw.get("limitations", [])
        if (
            not isinstance(answer, str)
            or not 1 <= len(answer) <= 4000
            or not isinstance(citations, list)
            or not all(isinstance(item, str) for item in citations)
            or len(citations) > 10
            or not isinstance(limitations, list)
            or not all(isinstance(item, str) for item in limitations)
            or len(limitations) > 10
        ):
            raise ApiError(
                502,
                "MODEL_BAD_OUTPUT",
                "模型返回的问答格式异常，请重试。",
                retryable=True,
                details={"reason": "ask_validation_failed"},
            )
        return {
            "id": new_id("qa"),
            "question": payload.question,
            "answer": answer,
            "citations": citations,
            "limitations": limitations,
            "created_at": _now(),
        }