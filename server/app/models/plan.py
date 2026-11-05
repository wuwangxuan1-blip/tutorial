from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..enums import Domain, Phase
from .session import StepTimer


class PrepDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=500)
    optional: bool = False


class StepDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phase: Phase
    title: str = Field(min_length=1, max_length=100)
    instruction: str = Field(min_length=1, max_length=2000)
    why: str = Field(default="", max_length=1000)
    duration_s: int = Field(default=0, ge=0, le=7200)
    completion_criteria: list[str] = Field(min_length=1, max_length=5)
    safety: list[str] = Field(default_factory=list, max_length=5)
    common_mistakes: list[str] = Field(default_factory=list, max_length=5)
    timer: StepTimer | None = None
    visual_aid: dict[str, Any] | None = None
    evidence_hint: str = Field(default="", max_length=300)
    media_prompt: str = Field(default="", max_length=300)

    @field_validator("completion_criteria")
    @classmethod
    def validate_criteria(cls, values: list[str]) -> list[str]:
        for item in values:
            if not 1 <= len(item) <= 300:
                raise ValueError("criterion length must be 1-300")
        return values


class PlanDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=120)
    summary: str = Field(default="", max_length=1000)
    assumptions: list[str] = Field(default_factory=list, max_length=10)
    preparation: list[PrepDraft] = Field(min_length=1, max_length=20)
    steps: list[StepDraft] = Field(min_length=3, max_length=15)
    total_estimated_min: int = Field(ge=5, le=480)
    safety_notes: list[str] = Field(default_factory=list, max_length=10)


class Preparation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    text: str = Field(min_length=1, max_length=500)
    optional: bool = False


class Step(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    order: int = Field(ge=1, le=15)
    phase: Phase
    title: str = Field(min_length=1, max_length=100)
    instruction: str = Field(min_length=1, max_length=2000)
    why: str = Field(default="", max_length=1000)
    duration_s: int = Field(ge=0, le=7200)
    completion_criteria: list[str] = Field(min_length=1, max_length=5)
    safety: list[str] = Field(default_factory=list, max_length=5)
    common_mistakes: list[str] = Field(default_factory=list, max_length=5)
    timer: StepTimer | None = None
    visual_aid: dict[str, Any] | None = None
    evidence_hint: str = Field(default="", max_length=300)
    media_prompt: str = Field(default="", max_length=300)


class PlanOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    session_id: str
    version: int = Field(ge=1)
    domain: Domain
    title: str = Field(min_length=1, max_length=120)
    summary: str = Field(default="", max_length=1000)
    assumptions: list[str] = Field(default_factory=list, max_length=10)
    preparation: list[Preparation] = Field(min_length=1, max_length=20)
    steps: list[Step] = Field(min_length=3, max_length=15)
    total_estimated_min: int = Field(ge=5, le=480)
    safety_notes: list[str] = Field(default_factory=list, max_length=10)
    reference_ids: list[str] = Field(default_factory=list)
    created_at: str