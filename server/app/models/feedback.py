from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MotionMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method: str = Field(min_length=1, max_length=100)
    sample_fps: int = Field(ge=1, le=30)
    frame_count: int = Field(ge=0, le=300)
    mean_translation_px: float = Field(ge=0)
    p95_translation_px: float = Field(ge=0)
    mean_rotation_deg: float = Field(ge=0)
    direction_changes: int = Field(ge=0)
    limitations: list[str] = Field(min_length=1, max_length=8)


class ObservationEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")

    media_id: str
    kind: Literal["image", "video_frame"]
    frame_index: int | None = Field(default=None, ge=0)
    timestamp_s: float | None = Field(default=None, ge=0)


class Observation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=300)
    evidence: ObservationEvidence
    certainty: Literal["low", "medium", "high"]


class FeedbackAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1, max_length=1000)
    observations: list[Observation] = Field(default_factory=list, max_length=8)
    assessment: Literal["not_verified", "likely_met", "unclear", "not_met"]
    uncertainties: list[str] = Field(default_factory=list, max_length=5)
    limitations: list[str] = Field(default_factory=list, max_length=5)
    motion_metrics: MotionMetrics | None = None
    sampled_frame_timestamps_s: list[float] = Field(default_factory=list, max_length=8)
    audio_analyzed: Literal[False] = False
    audio_note: str = Field(default="本期不分析音频，也不生成转写。", max_length=200)


class FeedbackOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    session_id: str
    step_id: str
    plan_version: int = Field(ge=1)
    media_ids: list[str] = Field(min_length=1, max_length=4)
    analysis: FeedbackAnalysis
    suggested_actions: list[str] = Field(default_factory=list, max_length=5)
    follow_up_questions: list[str] = Field(default_factory=list, max_length=3)
    revision_id: str | None = None
    created_at: str


class FeedbackJobRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_id: str
    plan_version: int = Field(ge=1)
    media_ids: list[str] = Field(min_length=1, max_length=4)
    note: str = Field(default="", max_length=500)


class FeedbackListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[FeedbackOut]
    next_cursor: str | None = None


class FeedbackDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1, max_length=1000)
    observations: list[Observation] = Field(default_factory=list, max_length=8)
    assessment: Literal["not_verified", "likely_met", "unclear", "not_met"]
    uncertainties: list[str] = Field(default_factory=list, max_length=5)
    limitations: list[str] = Field(default_factory=list, max_length=5)
    suggested_actions: list[str] = Field(default_factory=list, max_length=5)
    follow_up_questions: list[str] = Field(default_factory=list, max_length=3)

    @model_validator(mode="after")
    def validate_evidence(self) -> "FeedbackDraft":
        for observation in self.observations:
            evidence = observation.evidence
            if evidence.kind == "image":
                if evidence.frame_index is not None or evidence.timestamp_s is not None:
                    raise ValueError("image evidence must not include frame fields")
            else:
                if evidence.frame_index is None or evidence.timestamp_s is None:
                    raise ValueError("video_frame evidence requires frame_index and timestamp_s")
        return self