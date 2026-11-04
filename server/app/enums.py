from __future__ import annotations

from enum import Enum


class Domain(str, Enum):
    cooking = "cooking"
    photography = "photography"
    software = "software"
    coffee = "coffee"


class SessionStatus(str, Enum):
    clarifying = "clarifying"
    ready = "ready"
    in_progress = "in_progress"
    paused = "paused"
    completed = "completed"
    abandoned = "abandoned"


class StepStatus(str, Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    done = "done"
    skipped = "skipped"


class EvidenceLevel(str, Enum):
    none = "none"
    self_reported = "self_reported"
    media_submitted = "media_submitted"
    model_observed = "model_observed"
    measured = "measured"
    not_verifiable = "not_verifiable"


class JobType(str, Enum):
    plan_generation = "plan_generation"
    reference_import = "reference_import"
    feedback_analysis = "feedback_analysis"
    plan_revision = "plan_revision"


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    succeeded = "succeeded"
    failed = "failed"
    cancelled = "cancelled"
    expired = "expired"


class QuestionKind(str, Enum):
    text = "text"
    number = "number"
    single_choice = "single_choice"
    multi_choice = "multi_choice"
    boolean = "boolean"


class Phase(str, Enum):
    prepare = "prepare"
    execute = "execute"
    verify = "verify"
    finish = "finish"


class TimerState(str, Enum):
    idle = "idle"
    running = "running"
    paused = "paused"
    finished = "finished"