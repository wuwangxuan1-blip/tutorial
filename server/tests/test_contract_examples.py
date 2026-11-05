from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.models.common import ErrorEnvelope
from app.models.job import JobOut
from app.models.plan import PlanOut
from app.models.session import CreateSessionRequest, Conditions, Question, SessionOut

EXAMPLES = Path(__file__).resolve().parents[2] / "contracts" / "examples"


def load(name: str):
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


def test_session_create_request_example_validates():
    payload = load("session_create_request.json")
    request = CreateSessionRequest.model_validate(payload)
    assert request.domain.value == "cooking"
    assert request.goal == "2 人份番茄鸡蛋面，30 分钟内完成"
    assert request.reference_ids == []
    assert request.conditions.skill_level == "beginner"
    assert request.conditions.time_budget_min == 30
    assert request.conditions.people == 2
    assert request.conditions.servings is None


def test_questions_example_validates_and_has_expected_enums():
    questions = [Question.model_validate(item) for item in load("questions.json")]
    assert len(questions) == 5
    assert [item.field for item in questions] == [
        "servings",
        "stove_type",
        "oven_available",
        "allergies",
        "available_equipment",
    ]
    assert all(item.id.startswith("q_") for item in questions)
    assert questions[1].kind.value == "single_choice"
    assert questions[1].options == ["gas", "induction", "electric", "none"]
    assert questions[0].unit == "份"
    assert questions[2].unit is None


def test_session_example_round_trips_through_pydantic():
    payload = load("session.json")
    session = SessionOut.model_validate(payload)
    dumped = session.model_dump(mode="json")
    assert dumped == payload
    assert dumped["status"] == "clarifying"
    assert dumped["current_plan_version"] is None
    assert dumped["progress"]["timer"] is None
    assert dumped["progress"]["evidence_levels"] == {}
    assert all(item["id"].startswith("q_") for item in dumped["questions"])


def test_plan_example_round_trips_and_has_observable_steps():
    payload = load("plan_cooking.json")
    plan = PlanOut.model_validate(payload)
    dumped = plan.model_dump(mode="json")
    assert dumped == payload
    assert 3 <= len(dumped["steps"]) <= 15
    assert [step["order"] for step in dumped["steps"]] == [1, 2, 3]
    assert all(step["completion_criteria"] for step in dumped["steps"])
    assert all(step["id"].startswith("step_") for step in dumped["steps"])
    assert all(item["id"].startswith("prep_") for item in dumped["preparation"])
    assert dumped["steps"][0]["visual_aid"] is None
    assert dumped["steps"][0]["timer"]["suggested_s"] == 300


def test_job_success_and_failure_examples_round_trip():
    success_payload = load("job.json")
    success = JobOut.model_validate(success_payload)
    assert success.model_dump(mode="json") == success_payload
    assert success.status.value == "succeeded"
    assert success.stage == "done"
    assert success.result == {"plan_id": "plan_01J9Z8M1AA", "plan_version": 1}
    assert success.error is None

    failure_payload = load("job_failed.json")
    failure = JobOut.model_validate(failure_payload)
    assert failure.model_dump(mode="json") == failure_payload
    assert failure.status.value == "failed"
    assert failure.error is not None
    assert failure.error["error"]["code"] == "MODEL_TIMEOUT"
    assert failure.error["error"]["retryable"] is True


def test_error_envelope_example_round_trips():
    payload = load("error_version_conflict.json")
    envelope = ErrorEnvelope.model_validate(payload)
    assert envelope.model_dump(mode="json") == payload
    assert envelope.error.code == "VERSION_CONFLICT"
    assert envelope.error.retryable is False
    assert envelope.error.retry_after_s is None
    assert envelope.error.details == {"current_plan_version": 2}
    assert envelope.error.request_id.startswith("req_")


def test_unknown_condition_field_and_invalid_enum_are_rejected():
    with pytest.raises(ValidationError):
        Conditions.model_validate({"skill_level": "beginner", "unknown": 1})
    with pytest.raises(ValidationError):
        Conditions.model_validate({"skill_level": "wizard"})
    with pytest.raises(ValidationError):
        Conditions.model_validate({"notes": ""})


def test_plan_example_rejects_invalid_phase_and_empty_criteria():
    payload = load("plan_cooking.json")
    payload["steps"][0]["phase"] = "cook"
    with pytest.raises(ValidationError):
        PlanOut.model_validate(payload)

    payload = load("plan_cooking.json")
    payload["steps"][0]["completion_criteria"] = []
    with pytest.raises(ValidationError):
        PlanOut.model_validate(payload)