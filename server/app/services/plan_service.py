from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError

from ..config import Settings
from ..errors import ApiError
from ..ids import new_id
from ..models.plan import PlanDraft, PlanOut
from .model_client import ModelClient
from .prompt_builder import build_cooking_user_prompt, build_repair_prompt, load_system_prompt

COOKING_KEY_CONDITIONS = ("skill_level", "time_budget_min", "people", "servings", "stove_type")

logger = logging.getLogger("tutorial_coach.plan")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _summarize_validation_error(exc: ValidationError) -> str:
    parts = []
    for item in exc.errors()[:8]:
        location = ".".join(str(part) for part in item.get("loc", ()))
        message = str(item.get("msg", "invalid"))
        parts.append(f"{location}: {message}")
    return "; ".join(parts)[:800]


class PlanService:
    def __init__(self, settings: Settings, model_client: ModelClient) -> None:
        self.settings = settings
        self.model_client = model_client

    async def generate_cooking_plan(self, session: dict[str, Any], version: int) -> dict[str, Any]:
        conditions = dict(session.get("conditions") or {})
        user_prompt = build_cooking_user_prompt(session["goal"], conditions, session["domain"])
        system_prompt = load_system_prompt("cooking")
        raw = await self.model_client.chat_json(system_prompt, user_prompt)
        draft = await self._validate_or_repair(raw, system_prompt, user_prompt, conditions)
        return self._build_plan(session, draft, version, conditions)

    async def _validate_or_repair(
        self,
        raw: dict[str, Any],
        system_prompt: str,
        user_prompt: str,
        conditions: dict[str, Any],
    ) -> PlanDraft:
        try:
            return PlanDraft.model_validate(raw)
        except ValidationError as first_error:
            summary = _summarize_validation_error(first_error)
            logger.warning(
                "model_plan_validation_failed",
                extra={"error_code": "MODEL_BAD_OUTPUT", "status": "repair"},
            )
            repaired = await self.model_client.chat_json(
                system_prompt,
                build_repair_prompt(user_prompt, summary),
            )
            try:
                return PlanDraft.model_validate(repaired)
            except ValidationError as second_error:
                logger.warning(
                    "model_plan_repair_failed",
                    extra={
                        "error_code": "MODEL_BAD_OUTPUT",
                        "status": "failed",
                    },
                )
                raise ApiError(
                    502,
                    "MODEL_BAD_OUTPUT",
                    "模型返回的计划格式异常，已重试一次仍失败。",
                    retryable=True,
                ) from second_error

    def _build_plan(
        self,
        session: dict[str, Any],
        draft: PlanDraft,
        version: int,
        conditions: dict[str, Any],
    ) -> dict[str, Any]:
        preparation = [
            {"id": f"prep_{index}", "text": item.text, "optional": item.optional}
            for index, item in enumerate(draft.preparation, start=1)
        ]
        steps = []
        for index, item in enumerate(draft.steps, start=1):
            steps.append(
                {
                    "id": f"step_{index}",
                    "order": index,
                    "phase": item.phase.value,
                    "title": item.title,
                    "instruction": item.instruction,
                    "why": item.why,
                    "duration_s": item.duration_s,
                    "completion_criteria": item.completion_criteria,
                    "safety": item.safety,
                    "common_mistakes": item.common_mistakes,
                    "timer": item.timer.model_dump(mode="json") if item.timer else None,
                    "visual_aid": item.visual_aid,
                    "evidence_hint": item.evidence_hint,
                    "media_prompt": item.media_prompt,
                }
            )
        assumptions = list(draft.assumptions)
        for name in COOKING_KEY_CONDITIONS:
            if conditions.get(name) is None:
                note = f"未提供 {name}，按常见情况假设。"
                if note not in assumptions:
                    assumptions.append(note)
        safety_notes = list(draft.safety_notes)
        if not any("生熟" in note for note in safety_notes):
            safety_notes.append("生熟食材分开；处理生鸡蛋后洗手。")
        if not any("内部温度" in note for note in safety_notes):
            safety_notes.append("图片无法判断食物内部温度或食用安全；请用温度计或按食品安全规范确认。")
        return PlanOut(
            id=new_id("plan"),
            session_id=session["id"],
            version=version,
            domain=session["domain"],
            title=draft.title,
            summary=draft.summary,
            assumptions=assumptions[:10],
            preparation=preparation,
            steps=steps,
            total_estimated_min=draft.total_estimated_min,
            safety_notes=safety_notes[:10],
            reference_ids=list(session.get("reference_ids") or []),
            created_at=_now(),
        ).model_dump(mode="json")