from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"
COOKING_KEY_CONDITIONS = ("skill_level", "time_budget_min", "people", "servings", "stove_type")
SOFTWARE_KEY_CONDITIONS = ("skill_level", "os")
SOFTWARE_OPTIONAL_CONDITIONS = ("os_version", "backup_available", "terminal_available")


def load_prompt(name: str) -> str:
    return (PROMPT_DIR / f"{name}.txt").read_text(encoding="utf-8")


def load_system_prompt(domain: str) -> str:
    return load_prompt(f"plan_{domain}")


def build_cooking_user_prompt(goal: str, conditions: dict[str, Any], domain: str) -> str:
    condition_text = json.dumps(conditions, ensure_ascii=False, sort_keys=True)
    missing = [name for name in COOKING_KEY_CONDITIONS if conditions.get(name) is None]
    missing_text = "、".join(missing) if missing else "无"
    return (
        f"领域：{domain}\n"
        f"用户目标：{goal}\n"
        f"已知条件（JSON）：{condition_text}\n"
        f"仍缺失的关键条件：{missing_text}\n"
        "请生成符合系统消息结构要求的完整 JSON。"
    )


def build_software_user_prompt(goal: str, conditions: dict[str, Any], domain: str) -> str:
    condition_text = json.dumps(conditions, ensure_ascii=False, sort_keys=True)
    missing = [name for name in SOFTWARE_KEY_CONDITIONS if conditions.get(name) is None]
    optional_missing = [
        name for name in SOFTWARE_OPTIONAL_CONDITIONS if conditions.get(name) is None
    ]
    return (
        f"领域：{domain}\n"
        f"用户目标：{goal}\n"
        f"已知条件（JSON）：{condition_text}\n"
        f"仍缺失的关键条件：{'、'.join(missing) if missing else '无'}\n"
        f"仍缺失的可选条件：{'、'.join(optional_missing) if optional_missing else '无'}\n"
        "请生成符合系统消息结构要求的完整 JSON。"
    )


def build_ask_user_prompt(
    goal: str,
    domain: str,
    step: dict[str, Any],
    question: str,
) -> str:
    return (
        f"领域：{domain}\n"
        f"用户目标：{goal}\n"
        f"当前步骤：{step.get('title')}\n"
        f"步骤说明：{step.get('instruction')}\n"
        f"完成标准：{json.dumps(step.get('completion_criteria') or [], ensure_ascii=False)}\n"
        f"用户问题：{question}\n"
        "请只输出 JSON：answer、citations、limitations。"
    )


def build_revision_user_prompt(
    session: dict[str, Any],
    plan: dict[str, Any],
    request_reason: str,
) -> str:
    progress = session.get("progress") or {}
    statuses = progress.get("step_statuses") or {}
    steps = [
        {
            "id": step["id"],
            "order": step["order"],
            "title": step["title"],
            "instruction": step["instruction"],
            "duration_s": step["duration_s"],
            "completion_criteria": step["completion_criteria"],
            "status": statuses.get(step["id"], "not_started"),
        }
        for step in plan["steps"]
    ]
    return (
        f"领域：{session['domain']}\n"
        f"用户目标：{session['goal']}\n"
        f"当前条件（JSON）：{json.dumps(session.get('conditions') or {}, ensure_ascii=False, sort_keys=True)}\n"
        f"当前计划版本：{plan['version']}\n"
        f"当前步骤（JSON）：{json.dumps(steps, ensure_ascii=False)}\n"
        f"修订原因：{request_reason}\n"
        "只能修改状态为 not_started 或 in_progress 的步骤；"
        "done 或 skipped 步骤不得改动。请只输出 JSON：{\"changes\": [...]}。"
    )


def build_repair_prompt(user_prompt: str, error_summary: str) -> str:
    return (
        f"{user_prompt}\n\n"
        f"上一次输出未通过结构校验：{error_summary}\n"
        "请修正后只输出完整 JSON，不要输出解释或 Markdown。"
    )