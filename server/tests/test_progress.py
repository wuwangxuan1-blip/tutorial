from __future__ import annotations

import asyncio

FULL_COOKING = {
    "skill_level": "beginner",
    "time_budget_min": 30,
    "people": 2,
    "servings": 2,
    "stove_type": "gas",
}

PLAN = {
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
        },
        {
            "phase": "execute",
            "title": "炒鸡蛋",
            "instruction": "热锅下油，倒入蛋液，凝固后盛出。",
            "why": "保持嫩度。",
            "duration_s": 120,
            "completion_criteria": ["蛋液大部分凝固", "没有焦黑"],
            "safety": ["油温高"],
        },
        {
            "phase": "finish",
            "title": "煮面合并",
            "instruction": "面条煮熟后与番茄鸡蛋拌匀。",
            "why": "完成收尾。",
            "duration_s": 240,
            "completion_criteria": ["面条无硬芯", "汤汁均匀包裹面条"],
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
        assert response.status_code == 200
        job = response.json()
        if job["status"] in ("succeeded", "failed", "cancelled"):
            return job
        await asyncio.sleep(0.05)
    raise AssertionError("job did not finish in time")


async def setup_plan(client, monkeypatch, domain="cooking", conditions=None, plan=None):
    async def fake_chat_json(system_prompt, user_prompt, model=None, timeout_s=None):
        return plan if plan is not None else PLAN

    monkeypatch.setattr(client.app.state.model_client, "chat_json", fake_chat_json)
    created = await client.post(
        "/v1/sessions",
        json={
            "domain": domain,
            "goal": "2 人份番茄鸡蛋面",
            "conditions": conditions or FULL_COOKING,
        },
    )
    session = created.json()
    response = await client.post(
        f"/v1/sessions/{session['id']}/plan-jobs",
        json={"base_plan_version": None},
    )
    assert response.status_code == 202, response.text
    job = await wait_job(client, response.json()["id"])
    assert job["status"] == "succeeded", job
    plan = await client.get(f"/v1/sessions/{session['id']}/plan")
    assert plan.status_code == 200
    return session, plan.json()


async def test_progress_done_is_self_reported_and_pause_blocks_writes(client, monkeypatch):
    session, _ = await setup_plan(client, monkeypatch)
    session_id = session["id"]

    first = await client.patch(
        f"/v1/sessions/{session_id}/progress",
        json={
            "base_plan_version": 1,
            "current_step_id": "step_1",
            "step_statuses": {"step_1": "in_progress"},
        },
    )
    assert first.status_code == 200, first.text
    assert first.json()["session"]["status"] == "in_progress"

    done = await client.patch(
        f"/v1/sessions/{session_id}/progress",
        json={
            "base_plan_version": 1,
            "step_statuses": {"step_1": "done"},
        },
    )
    assert done.status_code == 200, done.text
    progress = done.json()["progress"]
    assert progress["step_statuses"]["step_1"] == "done"
    assert progress["evidence_levels"]["step_1"] == "self_reported"

    paused = await client.post(f"/v1/sessions/{session_id}/pause")
    assert paused.status_code == 200
    assert paused.json()["status"] == "paused"

    blocked = await client.patch(
        f"/v1/sessions/{session_id}/progress",
        json={"base_plan_version": 1, "step_statuses": {"step_2": "in_progress"}},
    )
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "SESSION_PAUSED"

    resumed = await client.post(f"/v1/sessions/{session_id}/resume")
    assert resumed.status_code == 200
    assert resumed.json()["status"] == "in_progress"

    second = await client.patch(
        f"/v1/sessions/{session_id}/progress",
        json={"base_plan_version": 1, "step_statuses": {"step_2": "in_progress"}},
    )
    assert second.status_code == 200


async def test_progress_rejects_version_conflict_and_locked_step(client, monkeypatch):
    session, _ = await setup_plan(client, monkeypatch)
    session_id = session["id"]

    conflict = await client.patch(
        f"/v1/sessions/{session_id}/progress",
        json={"base_plan_version": 9, "step_statuses": {"step_1": "in_progress"}},
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "VERSION_CONFLICT"

    await client.patch(
        f"/v1/sessions/{session_id}/progress",
        json={"base_plan_version": 1, "step_statuses": {"step_1": "done"}},
    )
    locked = await client.patch(
        f"/v1/sessions/{session_id}/progress",
        json={"base_plan_version": 1, "step_statuses": {"step_1": "in_progress"}},
    )
    assert locked.status_code == 422
    assert locked.json()["error"]["details"]["reason"] == "step_status_locked"


async def test_progress_timer_requires_anchor_and_matching_step(client, monkeypatch):
    session, _ = await setup_plan(client, monkeypatch)
    session_id = session["id"]

    missing_anchor = await client.patch(
        f"/v1/sessions/{session_id}/progress",
        json={
            "base_plan_version": 1,
            "current_step_id": "step_1",
            "timer": {
                "step_id": "step_1",
                "state": "running",
                "duration_s": 300,
                "remaining_s": 300,
                "anchor_elapsed_ms": None,
                "saved_at_epoch_ms": 1793789100000,
                "updated_at": "2026-11-04T08:05:00Z",
            },
        },
    )
    assert missing_anchor.status_code == 422

    mismatch = await client.patch(
        f"/v1/sessions/{session_id}/progress",
        json={
            "base_plan_version": 1,
            "current_step_id": "step_1",
            "timer": {
                "step_id": "step_2",
                "state": "running",
                "duration_s": 300,
                "remaining_s": 300,
                "anchor_elapsed_ms": 1000,
                "saved_at_epoch_ms": 1793789100000,
                "updated_at": "2026-11-04T08:05:00Z",
            },
        },
    )
    assert mismatch.status_code == 422
    assert mismatch.json()["error"]["details"]["reason"] == "timer_step_mismatch"


async def test_complete_keeps_other_steps_unfinished(client, monkeypatch):
    session, _ = await setup_plan(client, monkeypatch)
    session_id = session["id"]

    await client.patch(
        f"/v1/sessions/{session_id}/progress",
        json={"base_plan_version": 1, "step_statuses": {"step_1": "done"}},
    )
    completed = await client.post(
        f"/v1/sessions/{session_id}/complete",
        json={"rating": 4, "notes": "味道不错"},
    )
    assert completed.status_code == 200, completed.text
    body = completed.json()
    assert body["session"]["status"] == "completed"
    assert body["outcome"]["verification"] == "user_reported"
    statuses = body["session"]["progress"]["step_statuses"]
    assert statuses["step_1"] == "done"
    assert "step_2" not in statuses
    assert "step_3" not in statuses


async def test_abandon_marks_terminal(client, monkeypatch):
    session, _ = await setup_plan(client, monkeypatch)
    response = await client.post(
        f"/v1/sessions/{session['id']}/abandon",
        json={"reason": "临时有事"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "abandoned"