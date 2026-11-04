from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..enums import Domain, EvidenceLevel, QuestionKind, SessionStatus, StepStatus, TimerState


class Question(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    field: str
    prompt: str = Field(min_length=1, max_length=300)
    kind: QuestionKind
    required: bool = False
    options: list[str] = Field(default_factory=list)
    unit: str | None = None
    help: str = Field(default="", max_length=300)

    @field_validator("options")
    @classmethod
    def validate_options(cls, options: list[str], info: Any) -> list[str]:
        kind = info.data.get("kind")
        if kind in (QuestionKind.single_choice, QuestionKind.multi_choice):
            if not 2 <= len(options) <= 12:
                raise ValueError("choice questions require 2-12 options")
        elif options:
            raise ValueError("non-choice questions must not have options")
        return options


class AnswerItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_id: str = Field(min_length=1)
    value: Any


class AnswerSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answers: list[AnswerItem] = Field(min_length=1, max_length=10)


class Conditions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    skill_level: Literal["beginner", "intermediate", "advanced"] | None = None
    time_budget_min: int | None = Field(default=None, ge=10, le=480)
    people: int | None = Field(default=None, ge=1, le=20)
    dietary_preferences: list[str] | None = Field(default=None, max_length=10)
    allergies: list[str] | None = Field(default=None, max_length=10)
    available_equipment: list[str] | None = Field(default=None, max_length=20)
    environment: str | None = Field(default=None, min_length=1, max_length=200)
    notes: str | None = Field(default=None, min_length=1, max_length=500)
    servings: int | None = Field(default=None, ge=1, le=20)
    ingredients_available: list[str] | None = Field(default=None, max_length=30)
    oven_available: bool | None = None
    stove_type: Literal["gas", "induction", "electric", "none"] | None = None
    food_safety_notes: str | None = Field(default=None, min_length=1, max_length=500)
    device_model: str | None = Field(default=None, min_length=1, max_length=80)
    camera_app: str | None = Field(default=None, min_length=1, max_length=80)
    stabilization: Literal["none", "handheld", "gimbal", "tripod", "slider"] | None = None
    subject: str | None = Field(default=None, min_length=1, max_length=120)
    lighting: Literal["natural", "indoor", "studio", "mixed", "low_light"] | None = None
    aspect_ratio: Literal["9:16", "16:9", "1:1", "4:3"] | None = None
    location_constraints: str | None = Field(default=None, min_length=1, max_length=300)
    os: Literal["windows", "macos", "linux", "android", "ios"] | None = None
    os_version: str | None = Field(default=None, min_length=1, max_length=60)
    app_name: str | None = Field(default=None, min_length=1, max_length=80)
    app_version: str | None = Field(default=None, min_length=1, max_length=60)
    terminal_available: bool | None = None
    backup_available: bool | None = None
    risk_tolerance: Literal["low", "medium", "high"] | None = None
    brewer: str | None = Field(default=None, min_length=1, max_length=80)
    grinder: str | None = Field(default=None, min_length=1, max_length=80)
    scale_available: bool | None = None
    kettle_temp_control: bool | None = None
    beans: str | None = Field(default=None, min_length=1, max_length=120)
    roast_level: Literal["light", "medium", "medium_dark", "dark", "unknown"] | None = None
    taste_preference: list[str] | None = Field(default=None, max_length=10)
    milk_steamer: bool | None = None

    @field_validator(
        "dietary_preferences",
        "allergies",
        "available_equipment",
        "ingredients_available",
        "taste_preference",
    )
    @classmethod
    def validate_items(cls, values: list[str] | None, info: Any) -> list[str] | None:
        if values is None:
            return None
        limits = {
            "dietary_preferences": (10, 50),
            "allergies": (10, 50),
            "available_equipment": (20, 80),
            "ingredients_available": (30, 80),
            "taste_preference": (10, 50),
        }
        max_items, max_len = limits[info.field_name]
        if len(values) > max_items:
            raise ValueError("too many items")
        for item in values:
            if not 1 <= len(item) <= max_len:
                raise ValueError("invalid item length")
        return values


KEY_CONDITIONS = (
    "skill_level",
    "time_budget_min",
    "people",
    "servings",
    "stove_type",
    "stabilization",
    "aspect_ratio",
    "os",
    "brewer",
)


class StepTimer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    suggested_s: int = Field(ge=0, le=7200)
    auto_start: bool = False


class Timer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_id: str
    state: TimerState
    duration_s: int = Field(ge=1, le=7200)
    remaining_s: int = Field(ge=0, le=7200)
    anchor_elapsed_ms: int | None = Field(default=None, ge=0)
    saved_at_epoch_ms: int
    updated_at: str

    @field_validator("remaining_s")
    @classmethod
    def validate_remaining(cls, value: int, info: Any) -> int:
        duration = info.data.get("duration_s")
        if duration is not None and value > duration:
            raise ValueError("remaining_s must not exceed duration_s")
        return value

    @field_validator("anchor_elapsed_ms")
    @classmethod
    def validate_anchor(cls, value: int | None, info: Any) -> int | None:
        state = info.data.get("state")
        if state == TimerState.running and value is None:
            raise ValueError("running timer requires anchor_elapsed_ms")
        if state in (TimerState.idle, TimerState.paused, TimerState.finished) and value is not None:
            raise ValueError("non-running timer must not have anchor_elapsed_ms")
        return value


class Progress(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_step_id: str | None = None
    step_statuses: dict[str, StepStatus] = Field(default_factory=dict)
    evidence_levels: dict[str, EvidenceLevel] = Field(default_factory=dict)
    timer: Timer | None = None
    updated_at: str


class CreateSessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    domain: Domain
    goal: str = Field(min_length=1, max_length=500)
    reference_ids: list[str] = Field(default_factory=list)
    conditions: Conditions = Field(default_factory=Conditions)


class SessionOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    domain: Domain
    goal: str
    status: SessionStatus
    conditions: dict[str, Any]
    questions: list[Question]
    reference_ids: list[str]
    current_plan_version: int | None = None
    progress: Progress
    outcome: dict[str, Any] | None = None
    created_at: str
    updated_at: str


class CreatePlanJobRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    base_plan_version: int | None = None