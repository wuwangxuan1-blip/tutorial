from __future__ import annotations

from pathlib import Path
from typing import Any

from app.config import Settings
from app.services.plan_service import PlanService

MUSHROOM_DRAFT = {
    "title": "蘑菇汤",
    "summary": "清洗蘑菇，炒香后加水煮至熟软。",
    "assumptions": ["使用常见灶具和汤锅"],
    "preparation": [{"text": "蘑菇洗净切片。", "optional": False}],
    "steps": [
        {
            "phase": "prepare",
            "title": "清洗切片",
            "instruction": "蘑菇洗净后切片。",
            "why": "便于均匀受热。",
            "duration_s": 300,
            "completion_criteria": ["蘑菇表面无明显泥沙"],
            "safety": ["处理食材后洗手"],
        },
        {
            "phase": "execute",
            "title": "炒香",
            "instruction": "锅中放少量油，翻炒蘑菇至变软。",
            "why": "增加香气。",
            "duration_s": 300,
            "completion_criteria": ["蘑菇明显变软并出汁"],
            "safety": ["热油防溅"],
        },
        {
            "phase": "finish",
            "title": "加水煮熟",
            "instruction": "加水煮沸，确认蘑菇熟软后关火。",
            "why": "完成烹饪。",
            "duration_s": 600,
            "completion_criteria": ["汤面持续沸腾", "蘑菇中心熟软"],
            "safety": ["热汤防烫"],
        },
    ],
    "total_estimated_min": 20,
    "safety_notes": ["生熟分开", "热汤防烫"],
}


class FakeModelClient:
    def __init__(self, response: dict[str, Any]):
        self.response = response
        self.calls = 0

    async def chat_json(self, system_prompt, user_prompt, model=None, timeout_s=None):
        self.calls += 1
        return self.response


def make_service(tmp_path: Path) -> PlanService:
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
    return PlanService(settings, FakeModelClient(MUSHROOM_DRAFT))


def session_payload(goal: str, allergies: Any = None) -> dict[str, Any]:
    conditions: dict[str, Any] = {
        "skill_level": "beginner",
        "time_budget_min": 30,
        "people": 2,
        "servings": 2,
        "stove_type": "gas",
    }
    if allergies is not None:
        conditions["allergies"] = allergies
    return {
        "id": "sess_mushroom",
        "domain": "cooking",
        "goal": goal,
        "conditions": conditions,
        "reference_ids": [],
    }


async def test_allergy_assumption_is_generic_for_mushroom_soup(tmp_path):
    service = make_service(tmp_path)
    plan = await service.generate_cooking_plan(session_payload("蘑菇汤"), 1)
    allergy_notes = [item for item in plan["assumptions"] if "过敏" in item]
    assert len(allergy_notes) == 1
    assert "本次实际使用的食材和调味料" in allergy_notes[0]
    for forbidden in ("番茄", "鸡蛋", "面条"):
        assert forbidden not in allergy_notes[0]
    assert plan["title"] == "蘑菇汤"
    assert all(step["completion_criteria"] for step in plan["steps"])


async def test_explicit_no_allergies_skips_generic_allergy_note(tmp_path):
    service = make_service(tmp_path)
    plan = await service.generate_cooking_plan(
        session_payload("蘑菇汤", allergies=[]),
        1,
    )
    assert not any("未提供过敏信息" in item for item in plan["assumptions"])
    assert plan["title"] == "蘑菇汤"