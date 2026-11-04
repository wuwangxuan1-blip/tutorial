from __future__ import annotations

from typing import Any

from ..enums import Domain, QuestionKind
from ..models.session import Question

COOKING_KEY = ("skill_level", "time_budget_min", "people", "servings", "stove_type")
PHOTOGRAPHY_KEY = ("skill_level", "stabilization", "aspect_ratio")
SOFTWARE_KEY = ("skill_level", "os")
COFFEE_KEY = ("skill_level", "brewer")

KEY_FIELDS: dict[Domain, tuple[str, ...]] = {
    Domain.cooking: COOKING_KEY,
    Domain.photography: PHOTOGRAPHY_KEY,
    Domain.software: SOFTWARE_KEY,
    Domain.coffee: COFFEE_KEY,
}

OPTIONAL_FIELDS: dict[Domain, tuple[str, ...]] = {
    Domain.cooking: ("oven_available", "allergies", "available_equipment"),
    Domain.photography: ("device_model", "lighting", "subject"),
    Domain.software: ("os_version", "backup_available", "terminal_available"),
    Domain.coffee: ("grinder", "scale_available", "taste_preference"),
}

DEFINITIONS: dict[str, Question] = {
    "skill_level": Question(
        id="q_skill_level",
        field="skill_level",
        prompt="你目前的熟练程度是？",
        kind=QuestionKind.single_choice,
        required=True,
        options=["beginner", "intermediate", "advanced"],
        help="用于调整说明详细程度。",
    ),
    "time_budget_min": Question(
        id="q_time_budget",
        field="time_budget_min",
        prompt="你希望在多长时间内完成？",
        kind=QuestionKind.number,
        required=True,
        unit="分钟",
        help="包括准备和收尾；请填 10–480。",
    ),
    "people": Question(
        id="q_people",
        field="people",
        prompt="这次一共有几个人参与？",
        kind=QuestionKind.number,
        required=True,
        unit="人",
        help="用于估算份量和协作。",
    ),
    "servings": Question(
        id="q_servings",
        field="servings",
        prompt="需要做几人份？",
        kind=QuestionKind.number,
        required=True,
        unit="份",
        help="请填 1–20。",
    ),
    "stove_type": Question(
        id="q_stove_type",
        field="stove_type",
        prompt="你使用什么灶具？",
        kind=QuestionKind.single_choice,
        required=True,
        options=["gas", "induction", "electric", "none"],
        help="用于估算火力和时间。",
    ),
    "stabilization": Question(
        id="q_stabilization",
        field="stabilization",
        prompt="拍摄时如何稳定手机？",
        kind=QuestionKind.single_choice,
        required=True,
        options=["none", "handheld", "gimbal", "tripod", "slider"],
        help="用于选择运镜方式。",
    ),
    "aspect_ratio": Question(
        id="q_aspect_ratio",
        field="aspect_ratio",
        prompt="需要什么画幅？",
        kind=QuestionKind.single_choice,
        required=True,
        options=["9:16", "16:9", "1:1", "4:3"],
        help="用于构图和运镜示意。",
    ),
    "os": Question(
        id="q_os",
        field="os",
        prompt="你使用什么操作系统？",
        kind=QuestionKind.single_choice,
        required=True,
        options=["windows", "macos", "linux", "android", "ios"],
        help="用于给出对应菜单和命令。",
    ),
    "brewer": Question(
        id="q_brewer",
        field="brewer",
        prompt="你使用什么咖啡器具？",
        kind=QuestionKind.text,
        required=True,
        help="例如 V60、爱乐压、意式机。",
    ),
    "oven_available": Question(
        id="q_oven_available",
        field="oven_available",
        prompt="有可用的烤箱吗？",
        kind=QuestionKind.boolean,
        required=False,
        help="没有也可以生成灶具方案。",
    ),
    "allergies": Question(
        id="q_allergies",
        field="allergies",
        prompt="有哪些过敏或忌口？",
        kind=QuestionKind.text,
        required=False,
        help="没有可填“无”。",
    ),
    "available_equipment": Question(
        id="q_equipment",
        field="available_equipment",
        prompt="手边有哪些主要器具？",
        kind=QuestionKind.text,
        required=False,
        help="例如炒锅、汤锅、刀、砧板。",
    ),
    "device_model": Question(
        id="q_device_model",
        field="device_model",
        prompt="你使用什么手机或相机？",
        kind=QuestionKind.text,
        required=False,
        help="用于估算可用焦段。",
    ),
    "lighting": Question(
        id="q_lighting",
        field="lighting",
        prompt="现场光线如何？",
        kind=QuestionKind.single_choice,
        required=False,
        options=["natural", "indoor", "studio", "mixed", "low_light"],
        help="用于布光建议。",
    ),
    "subject": Question(
        id="q_subject",
        field="subject",
        prompt="主要拍摄主体是什么？",
        kind=QuestionKind.text,
        required=False,
        help="例如一杯咖啡。",
    ),
    "os_version": Question(
        id="q_os_version",
        field="os_version",
        prompt="系统版本是多少？",
        kind=QuestionKind.text,
        required=False,
        help="例如 Windows 11 23H2。",
    ),
    "backup_available": Question(
        id="q_backup",
        field="backup_available",
        prompt="操作前有可用备份吗？",
        kind=QuestionKind.boolean,
        required=False,
        help="涉及文件操作时建议先备份。",
    ),
    "terminal_available": Question(
        id="q_terminal",
        field="terminal_available",
        prompt="可以使用终端或 PowerShell 吗？",
        kind=QuestionKind.boolean,
        required=False,
        help="命令只作为文本提供，不会自动执行。",
    ),
    "grinder": Question(
        id="q_grinder",
        field="grinder",
        prompt="你使用什么磨豆机？",
        kind=QuestionKind.text,
        required=False,
        help="例如手磨型号。",
    ),
    "scale_available": Question(
        id="q_scale",
        field="scale_available",
        prompt="有电子秤吗？",
        kind=QuestionKind.boolean,
        required=False,
        help="用于控制粉水比。",
    ),
    "taste_preference": Question(
        id="q_taste_preference",
        field="taste_preference",
        prompt="你偏好什么风味？",
        kind=QuestionKind.text,
        required=False,
        help="例如偏酸、偏甜、坚果调。",
    ),
}


def build_questions(domain: Domain, conditions: dict[str, Any], round_no: int) -> list[Question]:
    if round_no >= 2:
        return []
    key_fields = KEY_FIELDS[domain]
    missing = [field for field in key_fields if conditions.get(field) is None]
    if not missing:
        return []
    questions = [DEFINITIONS[field] for field in missing if field in DEFINITIONS]
    if len(questions) < 3:
        for field in OPTIONAL_FIELDS[domain]:
            if len(questions) >= 5:
                break
            if conditions.get(field) is None and field in DEFINITIONS:
                questions.append(DEFINITIONS[field])
    if len(questions) < 3:
        return []
    return questions[:5]


def is_ready(domain: Domain, conditions: dict[str, Any], round_no: int) -> bool:
    return round_no >= 2 or not build_questions(domain, conditions, round_no)