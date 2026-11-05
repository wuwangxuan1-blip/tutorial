from __future__ import annotations

from test_progress import wait_job

SOFTWARE_CONDITIONS = {"skill_level": "beginner", "os": "windows"}

SOFTWARE_PLAN = {
    "title": "Windows 11 照片复制与按日期重命名",
    "summary": "先备份照片，再复制到新文件夹，最后按日期重命名并核对数量。",
    "assumptions": ["使用 Windows 11 文件资源管理器"],
    "preparation": [
        {"text": "确认照片所在文件夹与目标磁盘有足够空间。", "optional": False}
    ],
    "steps": [
        {
            "phase": "prepare",
            "title": "备份原始照片",
            "instruction": "把原始照片文件夹复制一份到另一个磁盘或云盘，确认备份完成后再继续。",
            "why": "避免误删或覆盖唯一副本。",
            "duration_s": 300,
            "completion_criteria": ["备份文件夹存在", "备份中的照片数量与原文件夹一致"],
            "safety": ["不要删除原始照片"],
        },
        {
            "phase": "execute",
            "title": "复制到新文件夹",
            "instruction": "在目标位置新建文件夹，选中照片后复制并粘贴；只使用文件资源管理器，不自动执行命令。",
            "why": "复制不会移动原文件。",
            "duration_s": 180,
            "completion_criteria": ["目标文件夹中出现全部照片", "照片数量与原文件夹一致"],
            "safety": ["操作前已备份"],
        },
        {
            "phase": "verify",
            "title": "按日期重命名并核对",
            "instruction": "选中照片后使用重命名功能，把名称改为包含拍摄日期的格式，例如 2026-11-05_照片。逐张核对文件名包含日期。",
            "why": "便于按日期查找。",
            "duration_s": 300,
            "completion_criteria": ["每个文件名都包含日期", "照片数量与备份一致"],
            "safety": ["不要覆盖同名文件"],
        },
    ],
    "total_estimated_min": 20,
    "safety_notes": ["涉及文件操作前先备份", "命令只作为教学文本"],
}


async def create_software_session(client, conditions):
    return await client.post(
        "/v1/sessions",
        json={
            "domain": "software",
            "goal": "在 Windows 11 中把照片复制到新文件夹，并按日期重命名",
            "conditions": conditions,
        },
    )


async def test_software_session_asks_os_and_skill_level(client):
    response = await create_software_session(client, conditions={})
    assert response.status_code == 201
    session = response.json()
    assert session["status"] == "clarifying"
    fields = {question["field"] for question in session["questions"]}
    assert {"skill_level", "os"}.issubset(fields)
    assert 3 <= len(session["questions"]) <= 5


async def test_software_plan_has_backup_text_and_verification(client, monkeypatch):
    async def fake_chat_json(system_prompt, user_prompt, model=None, timeout_s=None):
        assert "软件" in system_prompt or "文件" in system_prompt
        return SOFTWARE_PLAN

    monkeypatch.setattr(client.app.state.model_client, "chat_json", fake_chat_json)
    created = await create_software_session(client, SOFTWARE_CONDITIONS)
    assert created.status_code == 201
    session = created.json()
    assert session["status"] == "ready"

    response = await client.post(
        f"/v1/sessions/{session['id']}/plan-jobs",
        json={"base_plan_version": None},
    )
    assert response.status_code == 202, response.text
    job = await wait_job(client, response.json()["id"])
    assert job["status"] == "succeeded", job

    plan_response = await client.get(f"/v1/sessions/{session['id']}/plan")
    assert plan_response.status_code == 200
    plan = plan_response.json()
    assert plan["domain"] == "software"
    assert 3 <= len(plan["steps"]) <= 15
    assert plan["title"] == SOFTWARE_PLAN["title"]
    assert any("备份" in note for note in plan["assumptions"])
    assert any("不会自动执行" in note for note in plan["safety_notes"])
    assert plan["steps"][0]["title"] == "备份原始照片"
    assert all(step["completion_criteria"] for step in plan["steps"])


async def test_software_conditions_patch_and_locked_regeneration(client, monkeypatch):
    async def fake_chat_json(system_prompt, user_prompt, model=None, timeout_s=None):
        return SOFTWARE_PLAN

    monkeypatch.setattr(client.app.state.model_client, "chat_json", fake_chat_json)
    created = await create_software_session(client, SOFTWARE_CONDITIONS)
    session = created.json()
    await client.post(
        f"/v1/sessions/{session['id']}/plan-jobs",
        json={"base_plan_version": None},
    )
    # The fake model returns immediately; wait until the plan is visible.
    import asyncio

    for _ in range(100):
        plan = await client.get(f"/v1/sessions/{session['id']}/plan")
        if plan.status_code == 200:
            break
        await asyncio.sleep(0.05)
    assert plan.status_code == 200

    patched = await client.patch(
        f"/v1/sessions/{session['id']}/conditions",
        json={"base_plan_version": 1, "conditions": {"os_version": "Windows 11 23H2"}},
    )
    assert patched.status_code == 200
    assert patched.json()["impact"]["requires_regeneration"] is True

    await client.patch(
        f"/v1/sessions/{session['id']}/progress",
        json={"base_plan_version": 1, "step_statuses": {"step_1": "in_progress"}},
    )
    locked = await client.post(
        f"/v1/sessions/{session['id']}/plan-jobs",
        json={"base_plan_version": 1},
    )
    assert locked.status_code == 409
    assert locked.json()["error"]["code"] == "PLAN_LOCKED"