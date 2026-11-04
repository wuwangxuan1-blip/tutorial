from __future__ import annotations

import asyncio

FULL_COOKING = {
    "skill_level": "beginner",
    "time_budget_min": 30,
    "people": 2,
    "servings": 2,
    "stove_type": "gas",
}

MOCK_PLAN = {
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


async def wait_job(client, job_id: str, timeout_s: float = 8.0):
    deadline = asyncio.get_running_loop().time() + timeout_s
    while asyncio.get_running_loop().time() < deadline:
        response = await client.get(f"/v1/jobs/{job_id}")
        job = response.json()
        if job["status"] in ("succeeded", "failed", "cancelled"):
            return job
        await asyncio.sleep(0.05)
    raise AssertionError("job did not finish in time")


async def ready_session(client):
    response = await client.post(
        "/v1/sessions",
        json={"domain": "cooking", "goal": "2 人份番茄鸡蛋面", "conditions": FULL_COOKING},
    )
    assert response.status_code == 201
    assert response.json()["status"] == "ready"
    return response.json()


async def test_idempotency_same_key_same_body_returns_same_session(client):
    key = "idem-key-0000000001"
    payload = {"domain": "cooking", "goal": "2 人份番茄鸡蛋面", "conditions": FULL_COOKING}
    first = await client.post("/v1/sessions", json=payload, headers={"Idempotency-Key": key})
    second = await client.post("/v1/sessions", json=payload, headers={"Idempotency-Key": key})
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]


async def test_idempotency_same_key_different_body_conflicts(client):
    key = "idem-key-0000000002"
    first = await client.post(
        "/v1/sessions",
        json={"domain": "cooking", "goal": "2 人份番茄鸡蛋面", "conditions": FULL_COOKING},
        headers={"Idempotency-Key": key},
    )
    assert first.status_code == 201
    second = await client.post(
        "/v1/sessions",
        json={"domain": "cooking", "goal": "3 人份番茄鸡蛋面", "conditions": FULL_COOKING},
        headers={"Idempotency-Key": key},
    )
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"


async def test_idempotency_key_must_be_printable_ascii(client):
    response = await client.post(
        "/v1/sessions",
        json={"domain": "cooking", "goal": "2 人份番茄鸡蛋面", "conditions": FULL_COOKING},
        headers={"Idempotency-Key": "short-key"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_REQUEST"


async def test_plan_job_idempotency_replays_after_success(client, monkeypatch):
    calls = {"count": 0}

    async def fake_chat_json(system_prompt, user_prompt, model=None, timeout_s=None):
        calls["count"] += 1
        return MOCK_PLAN

    monkeypatch.setattr(client.app.state.model_client, "chat_json", fake_chat_json)
    session = await ready_session(client)
    key = "plan-idem-0000000001"
    first = await client.post(
        f"/v1/sessions/{session['id']}/plan-jobs",
        json={"base_plan_version": None},
        headers={"Idempotency-Key": key},
    )
    assert first.status_code == 202
    job = await wait_job(client, first.json()["id"])
    assert job["status"] == "succeeded"
    second = await client.post(
        f"/v1/sessions/{session['id']}/plan-jobs",
        json={"base_plan_version": None},
        headers={"Idempotency-Key": key},
    )
    assert second.status_code == 202
    assert second.json()["id"] == first.json()["id"]
    assert calls["count"] == 1


async def test_plan_job_idempotency_same_key_different_body_conflicts(client):
    session = await ready_session(client)
    key = "plan-idem-0000000002"
    first = await client.post(
        f"/v1/sessions/{session['id']}/plan-jobs",
        json={"base_plan_version": None},
        headers={"Idempotency-Key": key},
    )
    assert first.status_code == 202
    second = await client.post(
        f"/v1/sessions/{session['id']}/plan-jobs",
        json={"base_plan_version": 1},
        headers={"Idempotency-Key": key},
    )
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"