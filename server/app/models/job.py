from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ..enums import JobStatus, JobType


class JobOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    type: JobType
    status: JobStatus
    progress: int = Field(ge=0, le=100)
    stage: str = Field(max_length=40)
    session_id: str
    created_at: str
    updated_at: str
    expires_at: str
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None