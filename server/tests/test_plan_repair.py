from __future__ import annotations

from pathlib import Path

import pytest

from app.config import Settings
from app.errors import ApiError
from app.services.plan_service import PlanService

FULL_COOKING = {
    "skill_level": "beginner",
    "time_budget_min": 30,
    "people": 2,
    "servings": 2,
    "stove_type": "gas",
}

VALID_DRAFT = {
    "title": "番茄鸡蛋面",
    "summary": "先备料，再炒蛋和番茄，最后煮面。",
    "assumptions": ["使用家用燃气灶"],
    "preparation": [{"text": "番茄切块，鸡蛋打散。", "optional": False}],
    "steps": [
        {
            "phase": "prepare",
            "title": "烧水备料",
            "instruction": "烧水并切番茄。",
            "why": "缩短时间。",
            "duration_s": 300,
            "completion_criteria": ["水明显沸腾"],
            "safety": ["防烫"],
        },
        {
            "phase": "execute",
            "title": "炒鸡蛋",
            "instruction": "热锅下油，倒入蛋液。",
            "why": "保持嫩度。",
            "duration_s": 120,
            "completion_criteria": ["蛋液大部分凝固"],
            "safety": ["油温高"],
        },
        {
            "phase": "finish",
            "title": "煮面合并",
            "instruction": "煮面后与番茄鸡蛋拌匀。",
            "why": "完成。",
            "duration_s": 240,
            "completion_criteria": ["面条无硬芯"],
            "safety": ["防烫"],
        },
    ],
    "total_estimated_min": 30,
    "safety_notes": ["生熟分开"],
}

INVALID_DRAFT = {"title": "bad", "preparation": [], "steps": []}


class FakeModelClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    async def chat_json(self, system_prompt, user_prompt, model=None, timeout_s=None):
        self.calls += 1
        item = self.responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def make_service(tmp_path: Path, responses):
    settings = Settings(
        base_url="https://api.deepseek.com",
        api_key="test-key-not-used",
        text_model="deepseek-flash",
        vision_model="deepseek-flash",
        model_timeout_s=10.0,
        job_timeout_s=20.0,
        data_dir=tmp_path / "data",
        log_dir=tmp_path / "data" / "logs",
        queue_max=5,
    )
    fake = FakeModelClient(responses)
    return PlanService(settings, fake), fake


def session_payload():
    return {
        "id": "sess_test",
        "domain": "cooking",
        "goal": "2 人份番茄鸡蛋面",
        "conditions": FULL_COOKING,
        "reference_ids": [],
    }


async def test_invalid_then_valid_repair_returns_plan(tmp_path):
    service, fake = make_service(tmp_path, [INVALID_DRAFT, VALID_DRAFT])
    plan = await service.generate_cooking_plan(session_payload(), 1)
    assert fake.calls == 2
    assert plan["version"] == 1
    assert len(plan["steps"]) == 3
    assert all(step["completion_criteria"] for step in plan["steps"])
    assert any("过敏" in item for item in plan["assumptions"])
    assert any("器具" in item for item in plan["assumptions"])


async def test_two_invalid_drafts_fail_after_exactly_one_repair(tmp_path):
    service, fake = make_service(tmp_path, [INVALID_DRAFT, INVALID_DRAFT])
    with pytest.raises(ApiError) as error:
        await service.generate_cooking_plan(session_payload(), 1)
    assert fake.calls == 2
    assert error.value.code == "MODEL_BAD_OUTPUT"


async def test_repair_timeout_is_propagated(tmp_path):
    service, fake = make_service(
        tmp_path,
        [INVALID_DRAFT, ApiError(504, "MODEL_TIMEOUT", "模型请求超时。", retryable=True)],
    )
    with pytest.raises(ApiError) as error:
        await service.generate_cooking_plan(session_payload(), 1)
    assert fake.calls == 2
    assert error.value.code == "MODEL_TIMEOUT"

async def test_invalid_json_then_valid_repair_succeeds(tmp_path):
    service, fake = make_service(
        tmp_path,
        [
            ApiError(
                502,
                "MODEL_BAD_OUTPUT",
                "模型未返回可解析的 JSON。",
                retryable=True,
                details={"reason": "invalid_json"},
            ),
            VALID_DRAFT,
        ],
    )
    plan = await service.generate_cooking_plan(session_payload(), 1)
    assert fake.calls == 2
    assert len(plan["steps"]) == 3


async def test_invalid_json_twice_fails_after_exactly_one_repair(tmp_path):
    error = ApiError(
        502,
        "MODEL_BAD_OUTPUT",
        "模型未返回可解析的 JSON。",
        retryable=True,
        details={"reason": "invalid_json"},
    )
    service, fake = make_service(tmp_path, [error, error])
    with pytest.raises(ApiError) as caught:
        await service.generate_cooking_plan(session_payload(), 1)
    assert fake.calls == 2
    assert caught.value.code == "MODEL_BAD_OUTPUT"


async def test_model_refusal_is_not_repaired(tmp_path):
    service, fake = make_service(
        tmp_path,
        [ApiError(422, "MODEL_REFUSED", "模型拒绝处理该请求。")],
    )
    with pytest.raises(ApiError) as caught:
        await service.generate_cooking_plan(session_payload(), 1)
    assert fake.calls == 1
    assert caught.value.code == "MODEL_REFUSED"
