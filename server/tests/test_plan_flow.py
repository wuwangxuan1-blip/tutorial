from __future__ import annotations

import asyncio
from dataclasses import replace

import httpx

from app.errors import ApiError
from app.services.model_client import ModelClient

FULL_COOKING = {
    "skill_level": "beginner",
    "time_budget_min": 30,
    "people": 2,
    "servings": 2,
    "stove_type": "gas",
}


def mock_plan():
    return {
        "title": "番茄鸡蛋面",
        "summary": "先备料，再炒蛋和番茄，最后煮面合并。",
        "assumptions": ["使用家用燃气灶"],
        "preparation": [{"text": "番茄切块，鸡蛋打散。", "optional": False}],
        "steps": [
            {
                "phase": "prepare",
                "title": "烧水备料",
                "instruction": "汤锅加水烧开，同时切番茄、打散鸡蛋。",
                "why": "缩短总时间。",
                "duration_s": 300,
                "completion_criteria": ["水明显沸腾", "番茄切成约 2 cm 块"],
                "safety": ["防烫"],
                "common_mistakes": ["水未开就下面"],
                "timer": {"suggested_s": 300, "auto_start": False},
                "evidence_hint": "拍一张备料全景。",
                "media_prompt": "需要检查备料吗？",
            },
            {
                "phase": "execute",
                "title": "炒鸡蛋",
                "instruction": "热锅下油，倒入蛋液，凝固后盛出。",
                "why": "保持嫩度。",
                "duration_s": 120,
                "completion_criteria": ["蛋液大部分凝固", "没有焦黑"],
                "safety": ["油温高"],
                "common_mistakes": ["炒到全干"],
                "timer": {"suggested_s": 120, "auto_start": False},
                "evidence_hint": "拍锅中鸡蛋。",
                "media_prompt": "鸡蛋偏干还是偏嫩？",
            },
            {
                "phase": "finish",
                "title": "煮面合并",
                "instruction": "面条煮熟后与番茄鸡蛋拌匀。",
                "why": "完成收尾。",
                "duration_s": 240,
                "completion_criteria": ["面条无硬芯", "汤汁均匀包裹面条"],
                "safety": ["防烫"],
                "common_mistakes": ["面煮过头"],
                "timer": {"suggested_s": 240, "auto_start": False},
                "evidence_hint": "拍成品。",
                "media_prompt": "需要看成品状态吗？",
            },
        ],
        "total_estimated_min": 30,
        "safety_notes": ["生熟分开"],
    }


async def wait_job(client, job_id: str, timeout_s: float = 8.0):
    deadline = asyncio.get_running_loop().time() + timeout_s
    while asyncio.get_running_loop().time() < deadline:
        response = await client.get(f"/v1/jobs/{job_id}")
        assert response.status_code == 200
        job = response.json()
        if job["status"] in ("succeeded", "failed", "cancelled"):
            return job
        await asyncio.sleep(0.05)
    raise AssertionError("job did not finish in time")


async def test_plan_flow_with_mocked_model(client, monkeypatch):
    async def fake_chat_json(system_prompt, user_prompt, model=None, timeout_s=None):
        return mock_plan()

    monkeypatch.setattr(client.app.state.model_client, "chat_json", fake_chat_json)
    created = await client.post(
        "/v1/sessions",
        json={"domain": "cooking", "goal": "2 人份番茄鸡蛋面", "conditions": FULL_COOKING},
    )
    session = created.json()
    job_response = await client.post(
        f"/v1/sessions/{session['id']}/plan-jobs",
        json={"base_plan_version": None},
    )
    assert job_response.status_code == 202
    job = await wait_job(client, job_response.json()["id"])
    assert job["status"] == "succeeded", job
    assert job["result"]["plan_version"] == 1
    plan_response = await client.get(f"/v1/sessions/{session['id']}/plan")
    assert plan_response.status_code == 200
    plan = plan_response.json()
    assert 3 <= len(plan["steps"]) <= 15
    assert all(step["completion_criteria"] for step in plan["steps"])
    assert all(step["id"] == f"step_{index}" for index, step in enumerate(plan["steps"], start=1))


async def test_plan_job_without_key_fails_with_model_not_configured(client):
    created = await client.post(
        "/v1/sessions",
        json={"domain": "cooking", "goal": "2 人份番茄鸡蛋面", "conditions": FULL_COOKING},
    )
    session = created.json()
    job_response = await client.post(
        f"/v1/sessions/{session['id']}/plan-jobs",
        json={"base_plan_version": None},
    )
    assert job_response.status_code == 202
    job = await wait_job(client, job_response.json()["id"])
    assert job["status"] == "failed"
    assert job["error"]["error"]["code"] == "MODEL_NOT_CONFIGURED"
    plan_response = await client.get(f"/v1/sessions/{session['id']}/plan")
    assert plan_response.status_code == 404


async def test_plan_job_accepts_coffee_domain(client):
    created = await client.post(
        "/v1/sessions",
        json={
            "domain": "coffee",
            "goal": "手冲一杯咖啡",
            "conditions": {
                "skill_level": "beginner",
                "brewer": "V60",
            },
        },
    )
    session = created.json()
    assert session["status"] == "ready"
    job_response = await client.post(
        f"/v1/sessions/{session['id']}/plan-jobs",
        json={"base_plan_version": None},
    )
    assert job_response.status_code == 202
    job = await wait_job(client, job_response.json()["id"])
    assert job["status"] == "failed"
    assert job["error"]["error"]["code"] == "MODEL_NOT_CONFIGURED"

async def test_plan_job_surfaces_rate_limit_error(client, monkeypatch):
    async def fake_chat_json(system_prompt, user_prompt, model=None, timeout_s=None):
        raise ApiError(
            429,
            "MODEL_RATE_LIMITED",
            "模型限流，请稍后重试。",
            retryable=True,
            retry_after_s=3,
        )

    monkeypatch.setattr(client.app.state.model_client, "chat_json", fake_chat_json)
    created = await client.post(
        "/v1/sessions",
        json={"domain": "cooking", "goal": "2 人份番茄鸡蛋面", "conditions": FULL_COOKING},
    )
    session = created.json()
    response = await client.post(
        f"/v1/sessions/{session['id']}/plan-jobs",
        json={"base_plan_version": None},
    )
    assert response.status_code == 202
    job = await wait_job(client, response.json()["id"])
    assert job["status"] == "failed"
    assert job["error"]["error"]["code"] == "MODEL_RATE_LIMITED"
    assert job["error"]["error"]["retryable"] is True
    assert job["error"]["error"]["retry_after_s"] == 3


async def test_plan_job_structural_failure_after_one_repair(client, monkeypatch):
    calls = {"count": 0}

    async def fake_chat_json(system_prompt, user_prompt, model=None, timeout_s=None):
        calls["count"] += 1
        return {"title": "invalid plan"}

    monkeypatch.setattr(client.app.state.model_client, "chat_json", fake_chat_json)
    created = await client.post(
        "/v1/sessions",
        json={"domain": "cooking", "goal": "2 人份番茄鸡蛋面", "conditions": FULL_COOKING},
    )
    session = created.json()
    response = await client.post(
        f"/v1/sessions/{session['id']}/plan-jobs",
        json={"base_plan_version": None},
    )
    assert response.status_code == 202
    job = await wait_job(client, response.json()["id"])
    assert job["status"] == "failed"
    assert job["error"]["error"]["code"] == "MODEL_BAD_OUTPUT"
    assert calls["count"] == 2


async def test_two_invalid_json_http_responses_fail_job_with_retryable(client):
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {"content": "this is definitely not json"},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"total_tokens": 10},
            },
        )

    settings = replace(
        client.app.state.settings,
        api_key="test-key-value",
        text_model="deepseek-flash",
    )
    real_client = ModelClient(settings, transport=httpx.MockTransport(handler))
    client.app.state.model_client = real_client
    client.app.state.plan_service.model_client = real_client

    created = await client.post(
        "/v1/sessions",
        json={"domain": "cooking", "goal": "2 人份番茄鸡蛋面", "conditions": FULL_COOKING},
    )
    session = created.json()
    response = await client.post(
        f"/v1/sessions/{session['id']}/plan-jobs",
        json={"base_plan_version": None},
    )
    assert response.status_code == 202
    job = await wait_job(client, response.json()["id"])
    assert job["status"] == "failed"
    assert job["error"]["error"]["code"] == "MODEL_BAD_OUTPUT"
    assert job["error"]["error"]["retryable"] is True
    assert calls["count"] == 2
    plan_response = await client.get(f"/v1/sessions/{session['id']}/plan")
    assert plan_response.status_code == 404
