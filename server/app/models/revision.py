from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from ..enums import RevisionStatus
from .plan import PlanOut


class RevisionChange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    op: Literal["update", "add", "remove", "reorder"]
    step_id: str | None = None
    before: dict[str, Any] | None = None
    after: dict[str, Any] | None = None
    reason: str = Field(min_length=1, max_length=300)


class RevisionDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    changes: list[RevisionChange] = Field(default_factory=list, max_length=20)


class RevisionOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    session_id: str
    trigger: Literal["feedback", "conditions"]
    feedback_id: str | None = None
    request_reason: str | None = None
    base_plan_version: int
    status: RevisionStatus
    changes: list[RevisionChange]
    created_at: str
    applied_at: str | None = None
    rejected_at: str | None = None


class RevisionJobRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    feedback_id: str | None = None
    base_plan_version: int
    request_reason: str | None = Field(default=None, min_length=1, max_length=300)


class RevisionApplyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    base_plan_version: int


class RevisionRejectRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(default="", max_length=300)

class RevisionApplyResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan: PlanOut
    revision: RevisionOut