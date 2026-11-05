from __future__ import annotations

from test_progress import setup_plan


async def test_ask_returns_answer_for_current_step(client, monkeypatch):
    session, _ = await setup_plan(client, monkeypatch)
    calls = {"count": 0}

    async def fake_ask(system_prompt, user_prompt, model=None, timeout_s=None):
        calls["count"] += 1
        assert "烧水备料" in user_prompt
        return {
            "answer": "水明显沸腾后再下面；现在可以先检查锅底是否有大泡。",
            "citations": ["step_1"],
            "limitations": ["仅根据文字描述，未看到当前画面。"],
        }

    monkeypatch.setattr(client.app.state.model_client, "chat_json", fake_ask)
    response = await client.post(
        f"/v1/sessions/{session['id']}/ask",
        json={
            "question": "现在水算沸腾了吗？",
            "step_id": "step_1",
            "plan_version": 1,
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["answer"].startswith("水明显沸腾")
    assert body["citations"] == ["step_1"]
    assert body["limitations"]
    assert calls["count"] == 1


async def test_ask_rejects_version_mismatch_and_unknown_step(client, monkeypatch):
    session, _ = await setup_plan(client, monkeypatch)

    async def fake_ask(system_prompt, user_prompt, model=None, timeout_s=None):
        return {"answer": "可以。", "citations": [], "limitations": []}

    monkeypatch.setattr(client.app.state.model_client, "chat_json", fake_ask)
    version = await client.post(
        f"/v1/sessions/{session['id']}/ask",
        json={"question": "可以吗？", "step_id": "step_1", "plan_version": 9},
    )
    assert version.status_code == 409
    assert version.json()["error"]["code"] == "VERSION_CONFLICT"

    unknown = await client.post(
        f"/v1/sessions/{session['id']}/ask",
        json={"question": "可以吗？", "step_id": "step_99", "plan_version": 1},
    )
    assert unknown.status_code == 422
    assert unknown.json()["error"]["details"]["reason"] == "unknown_step"


async def test_ask_bad_output_and_timeout_are_explicit(client, monkeypatch):
    session, _ = await setup_plan(client, monkeypatch)

    async def bad_output(system_prompt, user_prompt, model=None, timeout_s=None):
        return {"answer": 123}

    monkeypatch.setattr(client.app.state.model_client, "chat_json", bad_output)
    bad = await client.post(
        f"/v1/sessions/{session['id']}/ask",
        json={"question": "可以吗？", "step_id": "step_1", "plan_version": 1},
    )
    assert bad.status_code == 502
    assert bad.json()["error"]["code"] == "MODEL_BAD_OUTPUT"
    assert bad.json()["error"]["retryable"] is True

    async def timeout(system_prompt, user_prompt, model=None, timeout_s=None):
        raise TimeoutError()

    monkeypatch.setattr(client.app.state.model_client, "chat_json", timeout)
    timed = await client.post(
        f"/v1/sessions/{session['id']}/ask",
        json={"question": "可以吗？", "step_id": "step_1", "plan_version": 1},
    )
    assert timed.status_code == 504
    assert timed.json()["error"]["code"] == "MODEL_TIMEOUT"