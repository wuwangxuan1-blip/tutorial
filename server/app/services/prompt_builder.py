from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"
COOKING_KEY_CONDITIONS = ("skill_level", "time_budget_min", "people", "servings", "stove_type")


def load_system_prompt(domain: str) -> str:
    return (PROMPT_DIR / f"plan_{domain}.txt").read_text(encoding="utf-8")


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


def build_repair_prompt(user_prompt: str, error_summary: str) -> str:
    return (
        f"{user_prompt}\n\n"
        f"上一次输出未通过结构校验：{error_summary}\n"
        "请修正后只输出完整 JSON，不要输出解释或 Markdown。"
    )