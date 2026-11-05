from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError

from ..config import Settings
from ..errors import ApiError
from ..ids import new_id
from ..models.camera import validate_visual_aid
from ..models.plan import PlanDraft, PlanOut
from .model_client import ModelClient
from .prompt_builder import (
    COFFEE_KEY_CONDITIONS,
    COFFEE_OPTIONAL_CONDITIONS,
    COOKING_KEY_CONDITIONS,
    PHOTOGRAPHY_KEY_CONDITIONS,
    PHOTOGRAPHY_OPTIONAL_CONDITIONS,
    SOFTWARE_KEY_CONDITIONS,
    SOFTWARE_OPTIONAL_CONDITIONS,
    build_coffee_user_prompt,
    build_cooking_user_prompt,
    build_photography_user_prompt,
    build_repair_prompt,
    build_software_user_prompt,
    load_system_prompt,
)

logger = logging.getLogger("tutorial_coach.plan")

SOFTWARE_OPTIONAL_ASSUMPTIONS = {
    "os_version": "未提供系统版本，按主流 Windows 11 版本假设。",
    "backup_available": "未提供备份情况，按操作前先复制一份备份处理。",
    "terminal_available": "未提供终端可用性，按图形界面操作为主假设。",
}


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

    async def generate_plan(self, session: dict[str, Any], version: int) -> dict[str, Any]:
        domain = session.get("domain")
        if domain == "cooking":
            return await self.generate_cooking_plan(session, version)
        if domain == "software":
            return await self.generate_software_plan(session, version)
        if domain == "photography":
            return await self.generate_photography_plan(session, version)
        if domain == "coffee":
            return await self.generate_coffee_plan(session, version)
        raise ApiError(
            422,
            "DOMAIN_MISMATCH",
            "本阶段仅启用烹饪、软件、摄影与咖啡领域的计划生成。",
        )

    async def generate_cooking_plan(self, session: dict[str, Any], version: int) -> dict[str, Any]:
        conditions = dict(session.get("conditions") or {})
        user_prompt = build_cooking_user_prompt(session["goal"], conditions, session["domain"])
        system_prompt = load_system_prompt("cooking")
        draft = await self._generate_draft(system_prompt, user_prompt)
        return self._build_plan(session, draft, version, conditions)

    async def generate_software_plan(self, session: dict[str, Any], version: int) -> dict[str, Any]:
        conditions = dict(session.get("conditions") or {})
        user_prompt = build_software_user_prompt(session["goal"], conditions, session["domain"])
        system_prompt = load_system_prompt("software")
        draft = await self._generate_draft(system_prompt, user_prompt)
        return self._build_plan(session, draft, version, conditions)

    async def generate_photography_plan(self, session: dict[str, Any], version: int) -> dict[str, Any]:
        conditions = dict(session.get("conditions") or {})
        user_prompt = build_photography_user_prompt(session["goal"], conditions, session["domain"])
        system_prompt = load_system_prompt("photography")
        draft = await self._generate_draft(system_prompt, user_prompt)
        return self._build_plan(session, draft, version, conditions)

    async def generate_coffee_plan(self, session: dict[str, Any], version: int) -> dict[str, Any]:
        conditions = dict(session.get("conditions") or {})
        user_prompt = build_coffee_user_prompt(session["goal"], conditions, session["domain"])
        system_prompt = load_system_prompt("coffee")
        draft = await self._generate_draft(system_prompt, user_prompt)
        return self._build_plan(session, draft, version, conditions)

    async def _generate_draft(self, system_prompt: str, user_prompt: str) -> PlanDraft:
        repair_summary: str | None = None
        try:
            raw = await self.model_client.chat_json(system_prompt, user_prompt)
            return PlanDraft.model_validate(raw)
        except ValidationError as first_error:
            repair_summary = _summarize_validation_error(first_error)
        except ApiError as first_error:
            if first_error.code != "MODEL_BAD_OUTPUT":
                raise
            reason = (first_error.details or {}).get("reason")
            if reason not in {"invalid_json", "empty_content"}:
                raise
            repair_summary = f"模型输出未通过 JSON 解析（{reason}）"
        logger.warning(
            "model_plan_validation_failed",
            extra={"error_code": "MODEL_BAD_OUTPUT", "status": "repair"},
        )
        repaired = await self.model_client.chat_json(
            system_prompt,
            build_repair_prompt(user_prompt, repair_summary or "输出不符合契约"),
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
        photography_visual_missing = False
        photography_fallback_used = False
        for index, item in enumerate(draft.steps, start=1):
            visual_aid = item.visual_aid
            if session["domain"] == "photography":
                if visual_aid is None:
                    photography_visual_missing = True
                else:
                    try:
                        visual_aid = validate_visual_aid(visual_aid)
                    except ValueError:
                        visual_aid = None
                        photography_visual_missing = True
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
                    "visual_aid": visual_aid,
                    "evidence_hint": item.evidence_hint,
                    "media_prompt": item.media_prompt,
                }
            )
        if session["domain"] == "photography" and not any(
            (step.get("visual_aid") or {}).get("type") == "camera_move"
            for step in steps
        ):
            orbit_index = next(
                (
                    idx
                    for idx, step in enumerate(steps)
                    if "环绕" in step["instruction"]
                    or "环绕" in step["title"]
                    or "绕" in step["instruction"]
                ),
                None,
            )
            if orbit_index is not None:
                fallback = self._fallback_orbit(
                    conditions,
                    int(steps[orbit_index]["duration_s"] or 8),
                )
                if fallback:
                    steps[orbit_index]["visual_aid"] = fallback
                    photography_visual_missing = False
                    photography_fallback_used = True

        assumptions = self._build_assumptions(draft, conditions, session["domain"])
        safety_notes = list(draft.safety_notes)
        if session["domain"] == "cooking":
            if not any("生熟" in note for note in safety_notes):
                safety_notes.append("生熟食材分开；处理生鸡蛋后洗手。")
            if not any("内部温度" in note for note in safety_notes):
                safety_notes.append("图片无法判断食物内部温度或食用安全；请用温度计或按食品安全规范确认。")
        elif session["domain"] == "photography":
            safety_notes.append("2D 路径与文字说明不代表真实焦距、景深或精确轨迹。")
            safety_notes.append("不提供 0–100 的稳定性评分；反馈只做定性观察。")
            safety_notes.append("本期不分析音频，也不生成转写。")
            if photography_fallback_used:
                safety_notes.append("运镜路径为服务端按步骤文字生成的结构化 2D 示意，不是模型输出，也不代表真实镜头。")
            elif photography_visual_missing:
                safety_notes.append("本步骤未提供合法运镜数据，无法播放动画；请按文字说明拍摄。")
        elif session["domain"] == "coffee":
            safety_notes.append("照片不能推断咖啡口味或萃取参数；口味评分与描述只来自用户。")
            safety_notes.append("每次调整只改一个变量，旧配方版本只读。")
        else:
            if not any("备份" in note for note in safety_notes):
                safety_notes.append("涉及文件操作前先复制一份备份，避免误删或覆盖。")
            if not any("自动执行" in note for note in safety_notes):
                safety_notes.append("命令和快捷键只作为教学文本，不会自动执行。")
        return PlanOut(
            id=new_id("plan"),
            session_id=session["id"],
            version=version,
            domain=session["domain"],
            title=draft.title,
            summary=draft.summary,
            assumptions=assumptions,
            preparation=preparation,
            steps=steps,
            total_estimated_min=draft.total_estimated_min,
            safety_notes=safety_notes[:10],
            reference_ids=list(session.get("reference_ids") or []),
            created_at=_now(),
        ).model_dump(mode="json")

    def _fallback_orbit(
        self,
        conditions: dict[str, Any],
        duration_s: int,
    ) -> dict[str, Any] | None:
        aspect = conditions.get("aspect_ratio")
        if aspect not in ("9:16", "16:9", "1:1", "4:3"):
            aspect = "9:16"
        technique = conditions.get("stabilization")
        if technique not in ("handheld", "gimbal", "tripod", "slider"):
            technique = "unknown"
        duration = 8 if duration_s >= 8 else max(2, duration_s)
        spec = {
            "id": "cam_orbit",
            "shot_type": "orbit_cw",
            "motion_type": "camera_move",
            "technique": technique,
            "subject_anchor": {"x": 0.5, "y": 0.5, "label": "主体"},
            "position_path": {
                "space": "normalized_top_down",
                "start": {"x": 0.3, "y": 0.7},
                "end": {"x": 0.7, "y": 0.3},
                "control": None,
                "arc": "cw",
            },
            "orientation_path": None,
            "zoom": None,
            "duration_s": duration,
            "easing": "ease_in_out",
            "aspect_ratio": aspect,
            "notes": ["服务端按步骤文字生成的结构化 2D 运镜示意。"],
            "limitations": ["2D 俯视示意，不代表真实焦距、景深或精确轨迹。"],
        }
        try:
            return validate_visual_aid({"type": "camera_move", "camera_move": spec})
        except ValueError:
            return None

    def _build_assumptions(
        self,
        draft: PlanDraft,
        conditions: dict[str, Any],
        domain: str,
    ) -> list[str]:
        model_assumptions: list[str] = []
        for note in draft.assumptions:
            if note not in model_assumptions:
                model_assumptions.append(note)

        if domain == "photography":
            generated_notes: list[str] = []
            for name in PHOTOGRAPHY_KEY_CONDITIONS:
                if conditions.get(name) is None:
                    note = f"未提供 {name}，按常见情况假设。"
                    if note not in model_assumptions:
                        generated_notes.append(note)
            optional_notes = {
                "device_model": "未提供 device_model（手机或相机型号），按常见手机广角镜头假设。",
                "lighting": "未提供 lighting（现场光线），按室内自然光与室内灯混合假设。",
                "subject": "未提供 subject（主体尺寸），按一杯咖啡作为画面主体假设。",
            }
            for name in PHOTOGRAPHY_OPTIONAL_CONDITIONS:
                if conditions.get(name) is None:
                    note = optional_notes[name]
                    if note not in model_assumptions and note not in generated_notes:
                        generated_notes.append(note)
            assumptions = list(model_assumptions[:10])
            for note in generated_notes:
                if len(assumptions) >= 10:
                    break
                if note not in assumptions:
                    assumptions.append(note)
            return assumptions

        if domain == "coffee":
            generated_notes: list[str] = []
            for name in COFFEE_KEY_CONDITIONS:
                if conditions.get(name) is None:
                    note = f"未提供 {name}，按 V60 手冲演示任务假设。"
                    if note not in model_assumptions:
                        generated_notes.append(note)
            optional_notes = {
                "grinder": "未提供磨豆机，可使用店家代磨并记录粗细；不要假设具体型号。",
                "scale_available": "未提供电子秤，可用量杯/量勺估算，但粉水比不精确。",
                "taste_preference": "未提供口味偏好，不预设风味结论。",
            }
            for name in COFFEE_OPTIONAL_CONDITIONS:
                if conditions.get(name) is None:
                    note = optional_notes[name]
                    if note not in model_assumptions and note not in generated_notes:
                        generated_notes.append(note)
            assumptions = list(model_assumptions[:10])
            for note in generated_notes:
                if len(assumptions) >= 10:
                    break
                if note not in assumptions:
                    assumptions.append(note)
            return assumptions

        if domain == "software":
            generated_notes: list[str] = []
            for name in SOFTWARE_KEY_CONDITIONS:
                if conditions.get(name) is None:
                    note = f"未提供 {name}，按常见情况假设。"
                    if note not in model_assumptions:
                        generated_notes.append(note)
            for name in SOFTWARE_OPTIONAL_CONDITIONS:
                if conditions.get(name) is None:
                    note = SOFTWARE_OPTIONAL_ASSUMPTIONS[name]
                    if note not in model_assumptions:
                        generated_notes.append(note)
            assumptions = list(model_assumptions[:10])
            for note in generated_notes:
                if len(assumptions) >= 10:
                    break
                if note not in assumptions:
                    assumptions.append(note)
            return assumptions

        generated_notes = []
        for name in COOKING_KEY_CONDITIONS:
            if conditions.get(name) is None:
                note = f"未提供 {name}，按常见情况假设。"
                if note not in model_assumptions and note not in generated_notes:
                    generated_notes.append(note)
        optional_assumptions = {
            "allergies": "未提供过敏信息，请核对本次实际使用的食材和调味料；无法确认是否存在过敏原。",
            "available_equipment": "未提供器具清单，按常见汤锅、炒锅、刀和砧板假设。",
            "oven_available": "未提供烤箱可用性，按以灶具为主的方案假设。",
        }
        for name, note in optional_assumptions.items():
            if name == "allergies":
                continue
            if (
                conditions.get(name) is None
                and note not in model_assumptions
                and note not in generated_notes
            ):
                generated_notes.append(note)

        allergy_note = optional_assumptions["allergies"]
        allergy_needed = conditions.get("allergies") is None
        allergy_already_present = allergy_note in model_assumptions
        reserve_for_allergy = 1 if allergy_needed and not allergy_already_present else 0

        assumptions = list(model_assumptions[: 10 - reserve_for_allergy])
        for note in generated_notes:
            if len(assumptions) >= 10 - reserve_for_allergy:
                break
            if note not in assumptions:
                assumptions.append(note)
        if allergy_needed and not allergy_already_present:
            assumptions.append(allergy_note)
        return assumptions