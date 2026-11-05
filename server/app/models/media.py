from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class MediaOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    kind: Literal["image", "video"]
    mime: str
    size_bytes: int = Field(ge=1)
    width: int = Field(ge=1)
    height: int = Field(ge=1)
    duration_s: float | None = Field(default=None, ge=0)
    sha256: str = Field(min_length=64, max_length=64)
    status: Literal["ready", "rejected"] = "ready"
    warnings: list[str] = Field(default_factory=list, max_length=5)
    created_at: str