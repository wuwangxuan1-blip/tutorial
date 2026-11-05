from __future__ import annotations

import copy

from test_progress import PLAN, setup_plan, wait_job


async def test_condition_revision_applies_to_unfinished_step_and_keeps_done_skipped(
    client,
    monkeypatch,
):
    session, plan = await setup_plan(client, monkeypatch)
    session_id = session["id"]
    await client.patch(
        f"/v1/sessions/{session_id}/progress",
        json={
            "base_plan_version": 1,
            "step_statuses": {"step_1": "done", "step_2": "skipped"},
        },
    )

    async def fake_revision(system_prompt, user_prompt, model=None, timeout_s=None):
        return {
            "changes": [
                {
                    "op": "update",
                    "step_id": "step_3",
                    "after": {"instruction": "面条煮熟后过冷水再与番茄鸡蛋拌匀。"},
                    "reason": "避免面条粘连。",
                }
            ]
        }

    monkeypatch.setattr(client.app.state.model_client, "chat_json", fake_revision)
    response = await client.post(
        f"/v1/sessions/{session_id}/revision-jobs",
        json={
            "feedback_id": None,
            "base_plan_version": 1,
            "request_reason": "只调整未完成的收尾步骤。",
        },
    )
    assert response.status_code == 202, response.text
    job = await wait_job(client, response.json()["id"])
    assert job["status"] == "succeeded", job
    revision_id = job["result"]["revision_id"]
    assert revision_id

    revisions = await client.get(f"/v1/sessions/{session_id}/revisions")
    assert revisions.status_code == 200
    revision = revisions.json()[0]
    assert revision["status"] == "proposed"
    assert revision["changes"][0]["before"]["instruction"] == plan["steps"][2]["instruction"]

    applied = await client.post(
        f"/v1/sessions/{session_id}/revisions/{revision_id}/apply",
        json={"base_plan_version": 1},
    )
    assert applied.status_code == 200, applied.text
    body = applied.json()
    assert body["plan"]["version"] == 2
    assert body["revision"]["status"] == "applied"
    assert body["plan"]["steps"][2]["instruction"] == "面条煮熟后过冷水再与番茄鸡蛋拌匀。"
    assert body["plan"]["steps"][0] == plan["steps"][0]
    assert body["plan"]["steps"][1] == plan["steps"][1]

    fresh = await client.get(f"/v1/sessions/{session_id}")
    assert fresh.status_code == 200
    state = fresh.json()
    assert state["current_plan_version"] == 2
    assert state["progress"]["step_statuses"]["step_1"] == "done"
    assert state["progress"]["step_statuses"]["step_2"] == "skipped"
    assert state["progress"]["evidence_levels"]["step_1"] == "self_reported"


async def test_revision_touching_done_step_fails_job_with_step_locked(client, monkeypatch):
    session, _ = await setup_plan(client, monkeypatch)
    session_id = session["id"]
    await client.patch(
        f"/v1/sessions/{session_id}/progress",
        json={"base_plan_version": 1, "step_statuses": {"step_1": "done"}},
    )

    async def fake_revision(system_prompt, user_prompt, model=None, timeout_s=None):
        return {
            "changes": [
                {
                    "op": "update",
                    "step_id": "step_1",
                    "after": {"instruction": "直接跳过烧水。"},
                    "reason": "尝试修改已完成步骤。",
                }
            ]
        }

    monkeypatch.setattr(client.app.state.model_client, "chat_json", fake_revision)
    response = await client.post(
        f"/v1/sessions/{session_id}/revision-jobs",
        json={
            "feedback_id": None,
            "base_plan_version": 1,
            "request_reason": "尝试修改已完成步骤。",
        },
    )
    assert response.status_code == 202
    job = await wait_job(client, response.json()["id"])
    assert job["status"] == "failed"
    assert job["error"]["error"]["code"] == "STEP_LOCKED"

    revisions = await client.get(f"/v1/sessions/{session_id}/revisions")
    assert revisions.json() == []


async def test_revision_reject_and_repeat_apply(client, monkeypatch):
    session, _ = await setup_plan(client, monkeypatch)
    session_id = session["id"]

    async def fake_revision(system_prompt, user_prompt, model=None, timeout_s=None):
        return {
            "changes": [
                {
                    "op": "update",
                    "step_id": "step_2",
                    "after": {"duration_s": 90},
                    "reason": "缩短炒制时间。",
                }
            ]
        }

    monkeypatch.setattr(client.app.state.model_client, "chat_json", fake_revision)
    response = await client.post(
        f"/v1/sessions/{session_id}/revision-jobs",
        json={
            "feedback_id": None,
            "base_plan_version": 1,
            "request_reason": "缩短炒制时间。",
        },
    )
    job = await wait_job(client, response.json()["id"])
    revision_id = job["result"]["revision_id"]

    rejected = await client.post(
        f"/v1/sessions/{session_id}/revisions/{revision_id}/reject",
        json={"reason": "我更习惯原来的时间。"},
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"

    again = await client.post(
        f"/v1/sessions/{session_id}/revisions/{revision_id}/apply",
        json={"base_plan_version": 1},
    )
    assert again.status_code == 409


async def test_revision_apply_version_conflict(client, monkeypatch):
    session, _ = await setup_plan(client, monkeypatch)
    session_id = session["id"]

    async def fake_revision(system_prompt, user_prompt, model=None, timeout_s=None):
        return {
            "changes": [
                {
                    "op": "update",
                    "step_id": "step_2",
                    "after": {"duration_s": 90},
                    "reason": "缩短炒制时间。",
                }
            ]
        }

    monkeypatch.setattr(client.app.state.model_client, "chat_json", fake_revision)
    response = await client.post(
        f"/v1/sessions/{session_id}/revision-jobs",
        json={
            "feedback_id": None,
            "base_plan_version": 1,
            "request_reason": "缩短炒制时间。",
        },
    )
    job = await wait_job(client, response.json()["id"])
    revision_id = job["result"]["revision_id"]
    conflict = await client.post(
        f"/v1/sessions/{session_id}/revisions/{revision_id}/apply",
        json={"base_plan_version": 2},
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "VERSION_CONFLICT"


async def test_revision_no_change_returns_null_revision(client, monkeypatch):
    session, _ = await setup_plan(client, monkeypatch)

    async def fake_revision(system_prompt, user_prompt, model=None, timeout_s=None):
        return {"changes": []}

    monkeypatch.setattr(client.app.state.model_client, "chat_json", fake_revision)
    response = await client.post(
        f"/v1/sessions/{session['id']}/revision-jobs",
        json={
            "feedback_id": None,
            "base_plan_version": 1,
            "request_reason": "无需调整。",
        },
    )
    job = await wait_job(client, response.json()["id"])
    assert job["status"] == "succeeded"
    assert job["stage"] == "no_change"
    assert job["result"]["revision_id"] is None

def plan_with_steps(count: int) -> dict:
    base = copy.deepcopy(PLAN)
    templates = PLAN["steps"]
    steps = []
    for index in range(1, count + 1):
        step = copy.deepcopy(templates[(index - 1) % len(templates)])
        step["title"] = f"步骤 {index}"
        steps.append(step)
    base["steps"] = steps
    base["title"] = f"{count} 步计划"
    return base


async def create_revision(client, monkeypatch, session_id: str, changes: list[dict]):
    async def fake_revision(system_prompt, user_prompt, model=None, timeout_s=None):
        return {"changes": changes}

    monkeypatch.setattr(client.app.state.model_client, "chat_json", fake_revision)
    response = await client.post(
        f"/v1/sessions/{session_id}/revision-jobs",
        json={
            "feedback_id": None,
            "base_plan_version": 1,
            "request_reason": "回归测试：校验修订后的完整计划。",
        },
    )
    assert response.status_code == 202, response.text
    job = await wait_job(client, response.json()["id"])
    assert job["status"] == "succeeded", job
    return job["result"]["revision_id"]


async def assert_plan_unchanged(client, session_id: str, expected_steps: int):
    session = await client.get(f"/v1/sessions/{session_id}")
    assert session.status_code == 200
    assert session.json()["current_plan_version"] == 1
    plan = await client.get(f"/v1/sessions/{session_id}/plan")
    assert plan.status_code == 200, plan.text
    assert plan.json()["version"] == 1
    assert len(plan.json()["steps"]) == expected_steps


async def test_revision_apply_rejects_remove_below_minimum(client, monkeypatch):
    session, _ = await setup_plan(client, monkeypatch)
    session_id = session["id"]
    revision_id = await create_revision(
        client,
        monkeypatch,
        session_id,
        [{"op": "remove", "step_id": "step_1", "reason": "删除第一步。"}],
    )

    applied = await client.post(
        f"/v1/sessions/{session_id}/revisions/{revision_id}/apply",
        json={"base_plan_version": 1},
    )
    assert applied.status_code == 422, applied.text
    assert applied.json()["error"]["code"] == "INVALID_REQUEST"
    assert applied.json()["error"]["details"]["reason"] == "revision_plan_invalid"

    await assert_plan_unchanged(client, session_id, expected_steps=3)
    revisions = await client.get(f"/v1/sessions/{session_id}/revisions")
    assert revisions.json()[0]["status"] == "proposed"


async def test_revision_apply_rejects_add_above_maximum(client, monkeypatch):
    plan = plan_with_steps(15)
    session, _ = await setup_plan(client, monkeypatch, plan=plan)
    session_id = session["id"]
    revision_id = await create_revision(
        client,
        monkeypatch,
        session_id,
        [
            {
                "op": "add",
                "after": {
                    "phase": "execute",
                    "title": "额外检查",
                    "instruction": "检查结果并记录。",
                    "why": "补充验证。",
                    "duration_s": 60,
                    "completion_criteria": ["结果可见"],
                    "safety": [],
                },
                "reason": "增加一步完成检查。",
            }
        ],
    )

    applied = await client.post(
        f"/v1/sessions/{session_id}/revisions/{revision_id}/apply",
        json={"base_plan_version": 1},
    )
    assert applied.status_code == 422, applied.text
    assert applied.json()["error"]["details"]["reason"] == "revision_plan_invalid"

    await assert_plan_unchanged(client, session_id, expected_steps=15)
    revisions = await client.get(f"/v1/sessions/{session_id}/revisions")
    assert revisions.json()[0]["status"] == "proposed"


async def test_revision_apply_rejects_combined_removes_below_minimum(client, monkeypatch):
    session, _ = await setup_plan(client, monkeypatch)
    session_id = session["id"]
    revision_id = await create_revision(
        client,
        monkeypatch,
        session_id,
        [
            {"op": "remove", "step_id": "step_1", "reason": "删除第一步。"},
            {"op": "remove", "step_id": "step_2", "reason": "删除第二步。"},
        ],
    )

    applied = await client.post(
        f"/v1/sessions/{session_id}/revisions/{revision_id}/apply",
        json={"base_plan_version": 1},
    )
    assert applied.status_code == 422, applied.text
    assert applied.json()["error"]["details"]["reason"] == "revision_plan_invalid"

    await assert_plan_unchanged(client, session_id, expected_steps=3)
    revisions = await client.get(f"/v1/sessions/{session_id}/revisions")
    assert revisions.json()[0]["status"] == "proposed"