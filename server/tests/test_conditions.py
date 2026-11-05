from __future__ import annotations

from test_progress import FULL_COOKING, PLAN, setup_plan, wait_job


async def create_session(client, conditions=None, goal="番茄鸡蛋面"):
    response = await client.post(
        "/v1/sessions",
        json={
            "domain": "cooking",
            "goal": goal,
            "conditions": conditions or FULL_COOKING,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


async def test_conditions_omitted_fields_keep_and_null_clears_optional(client):
    session = await create_session(
        client,
        conditions={**FULL_COOKING, "notes": "不吃香菜", "oven_available": False},
    )
    session_id = session["id"]

    cleared = await client.patch(
        f"/v1/sessions/{session_id}/conditions",
        json={"conditions": {"notes": None}},
    )
    assert cleared.status_code == 200, cleared.text
    body = cleared.json()
    assert "notes" not in body["session"]["conditions"]
    assert body["session"]["conditions"]["people"] == 2
    assert body["session"]["conditions"]["oven_available"] is False
    assert body["impact"]["changed_fields"] == ["notes"]

    updated = await client.patch(
        f"/v1/sessions/{session_id}/conditions",
        json={"conditions": {"people": 3}},
    )
    assert updated.status_code == 200
    assert updated.json()["session"]["conditions"]["people"] == 3
    assert updated.json()["session"]["conditions"]["time_budget_min"] == 30


async def test_conditions_key_null_is_atomic_rejection(client):
    session = await create_session(
        client,
        conditions={**FULL_COOKING, "notes": "不吃香菜"},
    )
    session_id = session["id"]

    rejected = await client.patch(
        f"/v1/sessions/{session_id}/conditions",
        json={"conditions": {"people": None, "notes": "改备注"}},
    )
    assert rejected.status_code == 422
    assert rejected.json()["error"]["details"]["field"] == "people"
    assert rejected.json()["error"]["details"]["reason"] == "key_condition_null"

    fresh = await client.get(f"/v1/sessions/{session_id}")
    assert fresh.status_code == 200
    assert fresh.json()["conditions"]["people"] == 2
    assert fresh.json()["conditions"]["notes"] == "不吃香菜"


async def test_conditions_empty_string_is_invalid(client):
    session = await create_session(client, conditions={**FULL_COOKING, "notes": "不吃香菜"})
    response = await client.patch(
        f"/v1/sessions/{session['id']}/conditions",
        json={"conditions": {"notes": ""}},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_REQUEST"


async def test_conditions_impact_requires_revision_after_progress(client, monkeypatch):
    session, _ = await setup_plan(client, monkeypatch)
    session_id = session["id"]
    await client.patch(
        f"/v1/sessions/{session_id}/progress",
        json={"base_plan_version": 1, "step_statuses": {"step_1": "in_progress"}},
    )

    response = await client.patch(
        f"/v1/sessions/{session_id}/conditions",
        json={"base_plan_version": 1, "conditions": {"time_budget_min": 20}},
    )
    assert response.status_code == 200, response.text
    impact = response.json()["impact"]
    assert impact["requires_revision"] is True
    assert impact["requires_regeneration"] is False

    locked = await client.post(
        f"/v1/sessions/{session_id}/plan-jobs",
        json={"base_plan_version": 1},
    )
    assert locked.status_code == 409
    assert locked.json()["error"]["code"] == "PLAN_LOCKED"


async def test_conditions_impact_allows_regeneration_without_progress(client, monkeypatch):
    session, _ = await setup_plan(client, monkeypatch)
    response = await client.patch(
        f"/v1/sessions/{session['id']}/conditions",
        json={"base_plan_version": 1, "conditions": {"time_budget_min": 20}},
    )
    assert response.status_code == 200
    impact = response.json()["impact"]
    assert impact["requires_regeneration"] is True
    assert impact["requires_revision"] is False


async def test_conditions_patch_requires_base_version_when_plan_exists(client, monkeypatch):
    session, _ = await setup_plan(client, monkeypatch)
    response = await client.patch(
        f"/v1/sessions/{session['id']}/conditions",
        json={"conditions": {"time_budget_min": 20}},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "VERSION_CONFLICT"


async def test_conditions_patch_does_not_revert_ready(client):
    session = await create_session(client)
    assert session["status"] == "ready"
    response = await client.patch(
        f"/v1/sessions/{session['id']}/conditions",
        json={"conditions": {"notes": None}},
    )
    assert response.status_code == 200
    assert response.json()["session"]["status"] == "ready"