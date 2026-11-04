from __future__ import annotations

import re
from typing import Any

from ..models.session import Question
from ..errors import invalid_request

ARRAY_FIELDS = {
    "dietary_preferences",
    "allergies",
    "available_equipment",
    "ingredients_available",
    "taste_preference",
}

EMPTY_VALUES = {"无", "没有", "none", "n/a", "na", "-"}


def normalize_condition_value(field: str, value: Any) -> Any:
    if field not in ARRAY_FIELDS or not isinstance(value, str):
        return value
    text = value.strip()
    if not text or text.lower() in EMPTY_VALUES:
        return []
    return [part.strip() for part in re.split(r"[,，、;；\n]+", text) if part.strip()]


def validate_answer(question: Question, value: Any) -> Any:
    if question.kind.value == "text":
        if not isinstance(value, str) or not 1 <= len(value) <= 500:
            raise invalid_request("文本回答长度必须为 1–500 字。", {"field": question.field})
        return value
    if question.kind.value == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise invalid_request("该问题需要填写数字。", {"field": question.field})
        if isinstance(value, float) and not value.is_integer():
            raise invalid_request("该问题需要填写整数。", {"field": question.field})
        return int(value)
    if question.kind.value == "boolean":
        if not isinstance(value, bool):
            raise invalid_request("该问题需要回答是或否。", {"field": question.field})
        return value
    if question.kind.value == "single_choice":
        if not isinstance(value, str) or value not in question.options:
            raise invalid_request("请选择有效选项。", {"field": question.field})
        return value
    if question.kind.value == "multi_choice":
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise invalid_request("该问题需要选择列表。", {"field": question.field})
        if any(item not in question.options for item in value):
            raise invalid_request("包含无效选项。", {"field": question.field})
        return value
    raise invalid_request("不支持的问题类型。", {"field": question.field})