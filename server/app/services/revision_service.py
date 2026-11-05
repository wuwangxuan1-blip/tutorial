from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError

from ..config import Settings
from ..enums import RevisionStatus, StepStatus
from ..errors import ApiError, invalid_request
from ..ids import new_id
from ..models.plan import PlanOut, Step, StepDraft
from ..models.revision import RevisionChange, RevisionDraft
from .model_client import ModelClient
from .prompt_builder import build_revision_user_prompt, load_prompt
from .store import JsonStore

LOCKED_STEP_STATUSES = (StepStatus.done.value, StepStatus.skipped.value)
UPDATE_FIELDS = {
    "phase",
    "title",
    "instruction",
    "why",
    "duration_s",
    "completion_criteria",
    "safety",
    "common_mistakes",
    "timer",
    "visual_aid",
    "evidence_hint",
    "media_prompt",
}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def locked_step_ids(session: dict[str, Any]) -> set[str]:
    statuses = (session.get("progress") or {}).get("step_statuses") or {}
    return {
        step_id
        for step_id, status in statuses.items()
        if status in LOCKED_STEP_STATUSES
    }


class RevisionService:
    def __init__(
        self,
        settings: Settings,
        model_client: ModelClient,
        store: JsonStore,
    ) -> None:
        self.settings = settings
        self.model_client = model_client
        self.store = store

    async def generate(
        self,
        session: dict[str, Any],
        plan: dict[str, Any],
        request_reason: str,
    ) -> dict[str, Any] | None:
        system_prompt = load_prompt("revision")
        user_prompt = build_revision_user_prompt(session, plan, request_reason)
        raw = await self.model_client.chat_json(system_prompt, user_prompt)
        try:
            draft = RevisionDraft.model_validate(raw)
        except ValidationError as exc:
            raise ApiError(
                502,
                "MODEL_BAD_OUTPUT",
                "模型返回的修订提议格式异常，请重试。",
                retryable=True,
                details={"reason": "revision_validation_failed"},
            ) from exc
        changes = draft.changes
        self._validate_changes(changes, session, plan)
        if not changes:
            return None
        revision = {
            "id": new_id("revision"),
            "session_id": session["id"],
            "trigger": "conditions",
            "feedback_id": None,
            "request_reason": request_reason,
            "base_plan_version": plan["version"],
            "status": RevisionStatus.proposed.value,
            "changes": [change.model_dump(mode="json") for change in changes],
            "created_at": _now(),
            "applied_at": None,
            "rejected_at": None,
        }
        await self.store.save_revision(revision)
        return revision

    def _validate_changes(
        self,
        changes: list[RevisionChange],
        session: dict[str, Any],
        plan: dict[str, Any],
        *,
        sequential: bool = False,
    ) -> None:
        steps = {step["id"]: step for step in plan["steps"]}
        original_ids = set(steps)
        available_ids = set(steps)
        remaining_count = len(steps)
        locked = locked_step_ids(session)
        for change in changes:
            if change.op in {"update", "remove", "reorder"}:
                known_ids = available_ids if sequential else original_ids
                if not change.step_id or change.step_id not in known_ids:
                    reason = (
                        "step_removed_by_revision"
                        if sequential and change.step_id in original_ids
                        else "unknown_step"
                    )
                    raise invalid_request(
                        "修订引用了已被删除或不存在的步骤。",
                        {"field": "changes.step_id", "reason": reason},
                    )
                if change.step_id in locked:
                    raise ApiError(
                        409,
                        "STEP_LOCKED",
                        "修订涉及已完成或已跳过的步骤，不能应用。",
                        details={"step_id": change.step_id},
                    )
            if change.op == "update":
                if not change.after:
                    raise invalid_request(
                        "update 修订必须提供 after。",
                        {"field": "changes.after", "reason": "missing_after"},
                    )
                unknown = set(change.after) - UPDATE_FIELDS
                if unknown:
                    raise invalid_request(
                        "修订只能修改步骤的可编辑字段。",
                        {"field": "changes.after", "reason": "field_not_editable"},
                    )
                if change.before is None:
                    change.before = {
                        key: steps[change.step_id].get(key) for key in change.after
                    }
                merged = dict(steps[change.step_id])
                merged.update(change.after)
                try:
                    Step.model_validate(merged)
                except ValidationError as exc:
                    raise invalid_request(
                        "修订后的步骤不符合契约。",
                        {"field": "changes.after", "reason": "invalid_step"},
                    ) from exc
            elif change.op == "add":
                if not change.after:
                    raise invalid_request(
                        "add 修订必须提供完整步骤。",
                        {"field": "changes.after", "reason": "missing_after"},
                    )
                draft_payload = {
                    key: value
                    for key, value in change.after.items()
                    if key not in {"id", "order"}
                }
                try:
                    StepDraft.model_validate(draft_payload)
                except ValidationError as exc:
                    raise invalid_request(
                        "新增步骤不符合契约。",
                        {"field": "changes.after", "reason": "invalid_step"},
                    ) from exc
                if sequential:
                    remaining_count += 1
            elif change.op == "remove":
                limit = remaining_count if sequential else len(steps)
                if limit <= 1:
                    raise invalid_request(
                        "不能删除最后一步。",
                        {"field": "changes.step_id", "reason": "last_step"},
                    )
                if sequential:
                    available_ids.discard(change.step_id)
                    remaining_count -= 1
            elif change.op == "reorder":
                if locked:
                    raise ApiError(
                        409,
                        "STEP_LOCKED",
                        "已有完成或跳过的步骤，不能重排计划。",
                    )
                order = (change.after or {}).get("order")
                limit = remaining_count if sequential else len(steps)
                if not isinstance(order, int) or not 1 <= order <= limit:
                    raise invalid_request(
                        "reorder 修订必须提供有效 order。",
                        {"field": "changes.after.order", "reason": "invalid_order"},
                    )

    async def apply(
        self,
        session: dict[str, Any],
        revision: dict[str, Any],
        base_plan_version: int,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        if revision["status"] != RevisionStatus.proposed.value:
            raise ApiError(409, "SESSION_NOT_EDITABLE", "修订已处理，不能重复应用。")
        current_version = session.get("current_plan_version")
        if current_version != base_plan_version or revision["base_plan_version"] != base_plan_version:
            raise ApiError(
                409,
                "VERSION_CONFLICT",
                "计划版本已变化，请刷新后重试。",
                details={"current_plan_version": current_version},
            )
        plan = await self.store.load_plan(session["id"], current_version)
        if not plan:
            raise ApiError(404, "NOT_FOUND", "当前计划不存在。")

        changes = [RevisionChange.model_validate(item) for item in revision["changes"]]
        self._validate_changes(changes, session, plan, sequential=True)

        new_plan = copy.deepcopy(plan)
        steps: list[dict[str, Any]] = new_plan["steps"]
        progress = dict(session.get("progress") or {})
        statuses = dict(progress.get("step_statuses") or {})
        evidences = dict(progress.get("evidence_levels") or {})
        current_step_id = progress.get("current_step_id")
        timer = progress.get("timer")

        for change in changes:
            if change.op == "update":
                target = next(step for step in steps if step["id"] == change.step_id)
                target.update(change.after or {})
                Step.model_validate(target)
            elif change.op == "add":
                payload = {
                    key: value
                    for key, value in (change.after or {}).items()
                    if key not in {"id", "order"}
                }
                draft = StepDraft.model_validate(payload)
                new_step = {
                    "id": new_id("step"),
                    "order": len(steps) + 1,
                    "phase": draft.phase.value,
                    "title": draft.title,
                    "instruction": draft.instruction,
                    "why": draft.why,
                    "duration_s": draft.duration_s,
                    "completion_criteria": draft.completion_criteria,
                    "safety": draft.safety,
                    "common_mistakes": draft.common_mistakes,
                    "timer": draft.timer.model_dump(mode="json") if draft.timer else None,
                    "visual_aid": draft.visual_aid,
                    "evidence_hint": draft.evidence_hint,
                    "media_prompt": draft.media_prompt,
                }
                steps.append(new_step)
            elif change.op == "remove":
                steps = [step for step in steps if step["id"] != change.step_id]
                statuses.pop(change.step_id, None)
                evidences.pop(change.step_id, None)
                if current_step_id == change.step_id:
                    current_step_id = None
                if timer and timer.get("step_id") == change.step_id:
                    timer = None
            elif change.op == "reorder":
                order = int((change.after or {})["order"])
                moving = next(step for step in steps if step["id"] == change.step_id)
                steps.remove(moving)
                steps.insert(order - 1, moving)

        for index, step in enumerate(steps, start=1):
            step["order"] = index
        new_version = current_version + 1
        new_plan["id"] = new_id("plan")
        new_plan["version"] = new_version
        new_plan["steps"] = steps
        new_plan["created_at"] = _now()

        try:
            PlanOut.model_validate(new_plan)
        except ValidationError as exc:
            raise invalid_request(
                "修订后的计划必须包含 3–15 个步骤且符合契约，未写入任何变更。",
                {"reason": "revision_plan_invalid"},
            ) from exc

        progress["step_statuses"] = statuses
        progress["evidence_levels"] = evidences
        progress["current_step_id"] = current_step_id
        progress["timer"] = timer
        progress["updated_at"] = _now()

        applied_revision = dict(revision)
        applied_revision["status"] = RevisionStatus.applied.value
        applied_revision["applied_at"] = _now()

        await self.store.save_plan(new_plan)
        session["current_plan_version"] = new_version
        session["progress"] = progress
        session["updated_at"] = _now()
        await self.store.save_session(session)
        await self.store.save_revision(applied_revision)
        return new_plan, applied_revision

    async def reject(
        self,
        revision: dict[str, Any],
        reason: str,
    ) -> dict[str, Any]:
        if revision["status"] != RevisionStatus.proposed.value:
            raise ApiError(409, "SESSION_NOT_EDITABLE", "修订已处理，不能重复拒绝。")
        revision = dict(revision)
        revision["status"] = RevisionStatus.rejected.value
        revision["rejected_at"] = _now()

        await self.store.save_revision(revision)
        return revision