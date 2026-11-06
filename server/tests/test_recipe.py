from __future__ import annotations

import copy

import pytest

from app.errors import ApiError
from test_progress import setup_plan

COFFEE_CONDITIONS = {"skill_level": "beginner", "brewer": "V60"}

COFFEE_PLAN = {
    "title": "V60 手冲练习（15 g / 225 g）",
    "summary": "准备参数、闷蒸、分段注水并记录口味。",
    "assumptions": ["使用 V60 滤杯"],
    "preparation": [
        {"text": "烧水至 92 °C，称取咖啡豆 15 g、水 225 g。", "optional": False},
    ],
    "steps": [
        {
            "phase": "prepare",
            "title": "准备器具与参数",
            "instruction": "咖啡粉 15 g，水 225 g，水温 92 °C，总时长 150 秒；折滤纸并温杯。",
            "why": "固定参数便于复现。",
            "duration_s": 60,
            "completion_criteria": ["粉水参数已称量", "滤纸已润湿"],
            "safety": ["注水时注意烫伤"],
        },
        {
            "phase": "execute",
            "title": "闷蒸与分段注水",
            "instruction": "先用 30 g 水闷蒸 30 秒，再分两次注水至 225 g，总时长约 150 秒。",
            "why": "让粉层均匀萃取。",
            "duration_s": 150,
            "completion_criteria": ["闷蒸 30 秒", "总注水约 150 秒"],
            "safety": [],
        },
        {
            "phase": "finish",
            "title": "品尝并记录",
            "instruction": "按自己的感受填写口味评分与描述，不根据照片推断口味。",
            "why": "为下一次单变量调整提供依据。",
            "duration_s": 60,
            "completion_criteria": ["已填写用户口味评分"],
            "safety": [],
        },
    ],
    "total_estimated_min": 15,
    "safety_notes": ["口味评分只来自用户输入。"],
}


async def setup_coffee(client, monkeypatch, plan=None):
    return await setup_plan(
        client,
        monkeypatch,
        domain="coffee",
        conditions=COFFEE_CONDITIONS,
        plan=copy.deepcopy(plan or COFFEE_PLAN),
    )


async def test_recipe_create_tasting_adjust_history_compare(client, monkeypatch):
    session, _ = await setup_coffee(client, monkeypatch)
    created = await client.post(
        f"/v1/sessions/{session['id']}/recipes",
        json={"base_plan_version": 1},
    )
    assert created.status_code == 201, created.text
    recipe = created.json()
    assert recipe["version"] == 1
    assert recipe["method"] == "pour_over"
    assert recipe["variables"]["dose_g"] == 15
    assert recipe["variables"]["water_g"] == 225
    assert recipe["variables"]["ratio"] == 15.0
    assert recipe["variables"]["water_temp_c"] == 92
    assert recipe["variables"]["brew_time_s"] == 150
    assert len(recipe["steps"]) == 3

    tasting = await client.post(
        f"/v1/recipes/{recipe['id']}/tastings",
        json={
            "sourness": 3,
            "sweetness": 2,
            "bitterness": 2,
            "body": 3,
            "aroma": 4,
            "aftertaste": 3,
            "overall": 3,
            "notes": "入口偏酸，余韵短。",
        },
    )
    assert tasting.status_code == 201, tasting.text
    tasting_id = tasting.json()["id"]

    adjusted = await client.post(
        f"/v1/recipes/{recipe['id']}/adjustments",
        json={
            "base_version": 1,
            "variable": "water_temp_c",
            "to_value": 90,
            "reason": "用户觉得偏酸，先只降低水温。",
            "tasting_id": tasting_id,
        },
    )
    assert adjusted.status_code == 201, adjusted.text
    body = adjusted.json()
    v2 = body["recipe"]
    assert v2["version"] == 2
    assert v2["id"] != recipe["id"]
    assert v2["variables"]["water_temp_c"] == 90
    assert v2["variables"]["water_g"] == 225
    assert body["adjustment"]["variable"] == "water_temp_c"
    assert body["adjustment"]["from_value"] == 92
    assert body["adjustment"]["to_value"] == 90
    assert any("90 °C" in step["instruction"] for step in v2["steps"])
    assert all("92 °C" not in step["instruction"] for step in v2["steps"])

    old = await client.get(f"/v1/recipes/{recipe['id']}")
    assert old.status_code == 200
    assert old.json()["variables"]["water_temp_c"] == 92
    assert any("92 °C" in step["instruction"] for step in old.json()["steps"])

    history = await client.get(f"/v1/recipes/{v2['id']}/history")
    assert history.status_code == 200, history.text
    versions = history.json()
    assert [item["version"] for item in versions] == [1, 2]
    assert versions[0]["tasting"]["id"] == tasting_id
    assert versions[1]["adjustment"]["variable"] == "water_temp_c"

    compare = await client.get(
        f"/v1/recipes/{recipe['id']}/compare",
        params={"against": v2["id"]},
    )
    assert compare.status_code == 200, compare.text
    comparison = compare.json()
    assert comparison["base"]["version"] == 1
    assert comparison["target"]["version"] == 2
    assert comparison["variable_diffs"] == [
        {
            "variable": "water_temp_c",
            "base_value": 92.0,
            "target_value": 90.0,
            "delta": -2.0,
        }
    ]
    assert comparison.get("tasting_comparison") is None
    assert any("缺少用户口味记录" in note for note in comparison["notes"])
    assert any("主动改变 water_temp_c" in note for note in comparison["notes"])

    tasting_v2 = await client.post(
        f"/v1/recipes/{v2['id']}/tastings",
        json={
            "sourness": 2,
            "sweetness": 3,
            "bitterness": 2,
            "body": 3,
            "aroma": 4,
            "aftertaste": 3,
            "overall": 4,
            "notes": "酸感降低。",
        },
    )
    assert tasting_v2.status_code == 201
    compare_with_tasting = await client.get(
        f"/v1/recipes/{recipe['id']}/compare",
        params={"against": v2["id"]},
    )
    tasting_comparison = compare_with_tasting.json()["tasting_comparison"]
    assert tasting_comparison["deltas"]["sourness"] == -1
    assert tasting_comparison["deltas"]["overall"] == 1


async def test_recipe_single_variable_and_version_conflicts_do_not_write(
    client,
    monkeypatch,
):
    session, _ = await setup_coffee(client, monkeypatch)
    recipe = (
        await client.post(
            f"/v1/sessions/{session['id']}/recipes",
            json={"base_plan_version": 1},
        )
    ).json()
    v2 = (
        await client.post(
            f"/v1/recipes/{recipe['id']}/adjustments",
            json={
                "base_version": 1,
                "variable": "water_temp_c",
                "to_value": 90,
                "reason": "只改水温。",
            },
        )
    ).json()["recipe"]

    multi = await client.post(
        f"/v1/recipes/{v2['id']}/adjustments",
        json={
            "base_version": 2,
            "variables": {"water_temp_c": 91, "water_g": 230},
            "reason": "尝试同时改两个变量。",
        },
    )
    assert multi.status_code == 422
    assert multi.json()["error"]["code"] == "SINGLE_VARIABLE_REQUIRED"

    same_value = await client.post(
        f"/v1/recipes/{v2['id']}/adjustments",
        json={
            "base_version": 2,
            "variable": "water_temp_c",
            "to_value": 90,
            "reason": "没有实际变化。",
        },
    )
    assert same_value.status_code == 422
    assert same_value.json()["error"]["code"] == "INVALID_REQUEST"
    assert same_value.json()["error"]["details"]["reason"] == "no_parameter_change"

    conflict = await client.post(
        f"/v1/recipes/{v2['id']}/adjustments",
        json={
            "base_version": 1,
            "variable": "water_temp_c",
            "to_value": 91,
            "reason": "使用旧版本。",
        },
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "VERSION_CONFLICT"
    assert conflict.json()["error"]["details"]["current_version"] == 2

    invalid = await client.post(
        f"/v1/recipes/{v2['id']}/adjustments",
        json={
            "base_version": 2,
            "variable": "water_temp_c",
            "to_value": 120,
            "reason": "超出范围。",
        },
    )
    assert invalid.status_code == 422

    history = (await client.get(f"/v1/recipes/{v2['id']}/history")).json()
    assert [item["version"] for item in history] == [1, 2]
    assert (await client.get(f"/v1/recipes/{recipe['id']}")).json()["version"] == 1

    non_coffee_session, _ = await setup_plan(client, monkeypatch)
    wrong_domain = await client.post(
        f"/v1/sessions/{non_coffee_session['id']}/recipes",
        json={"base_plan_version": 1},
    )
    assert wrong_domain.status_code == 422
    assert wrong_domain.json()["error"]["code"] == "DOMAIN_MISMATCH"


def _replace_plan_values(value, replacements):
    if isinstance(value, str):
        for old, new in replacements.items():
            value = value.replace(old, new)
        return value
    if isinstance(value, list):
        return [_replace_plan_values(item, replacements) for item in value]
    if isinstance(value, dict):
        return {key: _replace_plan_values(item, replacements) for key, item in value.items()}
    return value


def _with_params(plan, dose, water, temp, brew_time):
    replacements = {
        "15 g": f"{dose} g",
        "225 g": f"{water} g",
        "92 °C": f"{temp} °C",
        "150 秒": f"{brew_time} 秒",
    }
    return _replace_plan_values(copy.deepcopy(plan), replacements)


async def test_recipe_uses_confirmed_plan_parameters_and_demo_requires_matching_plan(
    client,
    monkeypatch,
):
    non_default = _with_params(COFFEE_PLAN, 18, 270, 90, 165)
    session, _ = await setup_coffee(client, monkeypatch, plan=non_default)
    created = await client.post(
        f"/v1/sessions/{session['id']}/recipes",
        json={"base_plan_version": 1, "demo": False},
    )
    assert created.status_code == 201, created.text
    recipe = created.json()
    assert recipe["variables"]["dose_g"] == 18
    assert recipe["variables"]["water_g"] == 270
    assert recipe["variables"]["ratio"] == 15.0
    assert recipe["variables"]["water_temp_c"] == 90
    assert recipe["variables"]["brew_time_s"] == 165
    instructions = " ".join(step["instruction"] for step in recipe["steps"])
    assert "18 g" in instructions
    assert "270 g" in instructions
    assert "90 °C" in instructions
    assert "165 秒" in instructions

    default_session, _ = await setup_coffee(client, monkeypatch)
    demo = await client.post(
        f"/v1/sessions/{default_session['id']}/recipes",
        json={"base_plan_version": 1, "demo": True},
    )
    assert demo.status_code == 201, demo.text
    demo_recipe = demo.json()
    assert demo_recipe["variables"]["dose_g"] == 15
    assert demo_recipe["variables"]["water_g"] == 225
    assert demo_recipe["variables"]["water_temp_c"] == 92
    assert demo_recipe["variables"]["brew_time_s"] == 150

    mismatch_session, _ = await setup_coffee(client, monkeypatch, plan=non_default)
    mismatch = await client.post(
        f"/v1/sessions/{mismatch_session['id']}/recipes",
        json={"base_plan_version": 1, "demo": True},
    )
    assert mismatch.status_code == 422
    assert mismatch.json()["error"]["details"]["reason"] == "demo_parameters_mismatch"
    assert (await client.get(f"/v1/sessions/{mismatch_session['id']}/recipes")).json() == []


async def test_water_only_adjustment_derives_ratio_and_rewrites_recipe(client, monkeypatch):
    session, _ = await setup_coffee(client, monkeypatch)
    recipe = (
        await client.post(
            f"/v1/sessions/{session['id']}/recipes",
            json={"base_plan_version": 1},
        )
    ).json()
    adjusted = await client.post(
        f"/v1/recipes/{recipe['id']}/adjustments",
        json={
            "base_version": 1,
            "variable": "water_g",
            "to_value": 240,
            "reason": "只改水量，观察粉水比派生变化。",
        },
    )
    assert adjusted.status_code == 201, adjusted.text
    body = adjusted.json()
    v2 = body["recipe"]
    assert body["adjustment"]["variable"] == "water_g"
    assert body["adjustment"]["from_value"] == 225
    assert body["adjustment"]["to_value"] == 240
    assert v2["variables"]["water_g"] == 240
    assert v2["variables"]["dose_g"] == 15
    assert v2["variables"]["ratio"] == 16.0
    water = next(item for item in v2["ingredients"] if item["name"] == "水")
    assert water["amount"] == 240
    assert any("240 g" in step["instruction"] for step in v2["steps"])
    assert all("225 g" not in step["instruction"] for step in v2["steps"])

    old = (await client.get(f"/v1/recipes/{recipe['id']}")).json()
    assert old["variables"]["water_g"] == 225
    assert old["variables"]["ratio"] == 15.0
    old_water = next(item for item in old["ingredients"] if item["name"] == "水")
    assert old_water["amount"] == 225
    assert any("225 g" in step["instruction"] for step in old["steps"])

    comparison = (
        await client.get(
            f"/v1/recipes/{recipe['id']}/compare",
            params={"against": v2["id"]},
        )
    ).json()
    diffs = {item["variable"]: item for item in comparison["variable_diffs"]}
    assert diffs["water_g"]["delta"] == 15.0
    assert diffs["ratio"]["delta"] == 1.0
    assert any("主动改变 water_g" in note for note in comparison["notes"])
    assert any("派生更新" in note for note in comparison["notes"])

    assert [item["version"] for item in (await client.get(f"/v1/recipes/{v2['id']}/history")).json()] == [1, 2]


async def test_derived_ratio_and_failed_adjustments_do_not_write(client, monkeypatch):
    session, _ = await setup_coffee(client, monkeypatch)
    recipe = (
        await client.post(
            f"/v1/sessions/{session['id']}/recipes",
            json={"base_plan_version": 1},
        )
    ).json()

    ratio_edit = await client.post(
        f"/v1/recipes/{recipe['id']}/adjustments",
        json={
            "base_version": 1,
            "variable": "ratio",
            "to_value": 16,
            "reason": "直接改粉水比。",
        },
    )
    assert ratio_edit.status_code == 422
    assert ratio_edit.json()["error"]["details"]["reason"] == "derived_variable"

    multi = await client.post(
        f"/v1/recipes/{recipe['id']}/adjustments",
        json={
            "base_version": 1,
            "variables": {"water_g": 240, "water_temp_c": 90},
            "reason": "同时改水量和水温。",
        },
    )
    assert multi.status_code == 422
    assert multi.json()["error"]["code"] == "SINGLE_VARIABLE_REQUIRED"

    invalid = await client.post(
        f"/v1/recipes/{recipe['id']}/adjustments",
        json={
            "base_version": 1,
            "variable": "water_temp_c",
            "to_value": 120,
            "reason": "无效水温。",
        },
    )
    assert invalid.status_code == 422
    assert (await client.get(f"/v1/sessions/{session['id']}/recipes")).json()[0]["version"] == 1


async def test_semantic_step_rewrite_keeps_rinse_water_and_same_value_variables(client, monkeypatch):
    plan_data = copy.deepcopy(COFFEE_PLAN)
    plan_data["steps"][0]["instruction"] = (
        "咖啡粉 15 g，温杯用水 115 g，水温 92 °C，总时长 150 秒；注水至 225 g。"
    )
    plan_data["steps"][1]["instruction"] = "闷蒸后注水至 225 g，总时长 150 秒。"
    session, _ = await setup_coffee(client, monkeypatch, plan=plan_data)
    recipe = (
        await client.post(
            f"/v1/sessions/{session['id']}/recipes",
            json={"base_plan_version": 1},
        )
    ).json()
    assert recipe["variables"]["dose_g"] == 15
    assert recipe["variables"]["water_g"] == 225
    assert "温杯用水 115 g" in recipe["steps"][0]["instruction"]

    adjusted = await client.post(
        f"/v1/recipes/{recipe['id']}/adjustments",
        json={
            "base_version": 1,
            "variable": "dose_g",
            "to_value": 16,
            "reason": "只改咖啡粉量。",
        },
    )
    assert adjusted.status_code == 201, adjusted.text
    v2 = adjusted.json()["recipe"]
    assert v2["variables"]["dose_g"] == 16
    assert v2["variables"]["water_g"] == 225
    assert v2["variables"]["ratio"] == 14.06
    assert "咖啡粉 16 g" in v2["steps"][0]["instruction"]
    assert "温杯用水 115 g" in v2["steps"][0]["instruction"]
    coffee = next(item for item in v2["ingredients"] if item["name"] == "咖啡豆")
    water = next(item for item in v2["ingredients"] if item["name"] == "水")
    assert coffee["amount"] == 16
    assert water["amount"] == 225

    old = (await client.get(f"/v1/recipes/{recipe['id']}")).json()
    assert old["variables"]["dose_g"] == 15
    assert "咖啡粉 15 g" in old["steps"][0]["instruction"]
    assert "温杯用水 115 g" in old["steps"][0]["instruction"]

    service = client.app.state.recipe_service
    same_value_steps = [
        {
            "id": "rst_1",
            "order": 1,
            "instruction": "咖啡粉 15 g，水 15 g，水温 15 °C，总时长 15 秒。",
            "duration_s": 1,
            "target": "咖啡粉 15 g",
        }
    ]
    same_value = service._rewrite_steps(
        same_value_steps,
        {"dose_g": 15, "water_g": 15, "water_temp_c": 15, "brew_time_s": 15, "ratio": 1.0},
        {"dose_g": 16, "water_g": 15, "water_temp_c": 15, "brew_time_s": 15, "ratio": 1.0},
    )
    text = same_value[0]["instruction"]
    assert "咖啡粉 16 g" in text
    assert "水 15 g" in text
    assert "水温 15 °C" in text
    assert "总时长 15 秒" in text
    assert "咖啡粉 16 g" in same_value[0]["target"]


async def test_chinese_brew_time_variants(client):
    service = client.app.state.recipe_service
    assert service._parse_brew_time("总时长约 3 分钟") == 180
    assert service._parse_brew_time("2 分 30 秒") == 150
    assert service._parse_brew_time("150 秒") == 150
    assert service._parse_brew_time("用时 30 秒。总时长 150 秒") == 150
    assert service._parse_brew_time("总时长 2 分 30 秒") == 150
    assert service._parse_brew_time("总时长：150 秒，闷蒸用时 30 秒") == 150
    assert service._parse_brew_time("闷蒸用时 30 秒，总时长：150 秒") == 150
    assert service._parse_brew_time("总时长: 2 分 30 秒，闷蒸用时 30 秒") == 150
    assert service._parse_brew_time("闷蒸用时 30 秒，总时长:150 秒") == 150


async def test_water_total_parser_prefers_explicit_total(client):
    service = client.app.state.recipe_service
    assert (
        service._parse_water_total("闷蒸 30 g，注水至 100 g，注水至 150 g，总水量 225 g")
        == 225
    )
    assert service._parse_water_total("闷蒸注水 30 g，继续注水至 225 g") == 225
    assert service._parse_water_total("水 225 g") == 225


async def test_adjustment_validates_values_before_ratio_derivation(client, monkeypatch):
    session, _ = await setup_coffee(client, monkeypatch)
    recipe = (
        await client.post(
            f"/v1/sessions/{session['id']}/recipes",
            json={"base_plan_version": 1},
        )
    ).json()

    dose_zero = await client.post(
        f"/v1/recipes/{recipe['id']}/adjustments",
        json={
            "base_version": 1,
            "variable": "dose_g",
            "to_value": 0,
            "reason": "非法粉量。",
        },
    )
    assert dose_zero.status_code == 422
    assert dose_zero.json()["error"]["details"]["reason"] == "invalid_adjustment_value"

    non_numeric = await client.post(
        f"/v1/recipes/{recipe['id']}/adjustments",
        json={
            "base_version": 1,
            "variable": "water_temp_c",
            "to_value": "abc",
            "reason": "非数字水温。",
        },
    )
    assert non_numeric.status_code == 422
    assert non_numeric.json()["error"]["details"]["reason"] == "invalid_adjustment_value"

    recipes = (await client.get(f"/v1/sessions/{session['id']}/recipes")).json()
    assert [item["version"] for item in recipes] == [1]
    assert (await client.get(f"/v1/recipes/{recipe['id']}")).json()["variables"]["dose_g"] == 15


def _controlled_plan(instruction: str) -> dict:
    plan = copy.deepcopy(COFFEE_PLAN)
    plan["title"] = "V60 参数解析测试"
    plan["summary"] = ""
    plan["preparation"] = [{"text": "准备器具与滤纸。", "optional": False}]
    plan["steps"][0]["instruction"] = instruction
    plan["steps"][1]["instruction"] = "按计划继续操作。"
    plan["steps"][2]["instruction"] = "完成后记录。"
    for step in plan["steps"]:
        step["completion_criteria"] = ["按说明完成"]
    return plan


async def test_recipe_water_total_uses_cumulative_water_and_rejects_ambiguous(client, monkeypatch):
    session, _ = await setup_coffee(
        client,
        monkeypatch,
        plan=_controlled_plan(
            "咖啡粉 15 g，闷蒸注水 30 g，继续注水至 225 g，水温 92 °C，总时长 150 秒。"
        ),
    )
    created = await client.post(
        f"/v1/sessions/{session['id']}/recipes",
        json={"base_plan_version": 1},
    )
    assert created.status_code == 201, created.text
    recipe = created.json()
    assert recipe["variables"]["dose_g"] == 15
    assert recipe["variables"]["water_g"] == 225
    assert recipe["variables"]["ratio"] == 15.0
    water = next(item for item in recipe["ingredients"] if item["name"] == "水")
    assert water["amount"] == 225

    ambiguous_session, _ = await setup_coffee(
        client,
        monkeypatch,
        plan=_controlled_plan(
            "咖啡粉 15 g，闷蒸注水 30 g，再注水 90 g，水温 92 °C，总时长 150 秒。"
        ),
    )
    ambiguous = await client.post(
        f"/v1/sessions/{ambiguous_session['id']}/recipes",
        json={"base_plan_version": 1},
    )
    assert ambiguous.status_code == 422
    assert ambiguous.json()["error"]["details"]["reason"] == "water_total_ambiguous"
    assert (await client.get(f"/v1/sessions/{ambiguous_session['id']}/recipes")).json() == []


async def test_recipe_explicit_total_time_wins_and_adjustment_rewrites_chinese_duration(
    client,
    monkeypatch,
):
    session, _ = await setup_coffee(
        client,
        monkeypatch,
        plan=_controlled_plan(
            "咖啡粉 15 g，水 225 g，水温 92 °C，闷蒸 30 秒。总时长 2 分 30 秒。"
        ),
    )
    recipe = (
        await client.post(
            f"/v1/sessions/{session['id']}/recipes",
            json={"base_plan_version": 1},
        )
    ).json()
    assert recipe["variables"]["brew_time_s"] == 150
    assert "总时长 2 分 30 秒" in recipe["steps"][0]["instruction"]

    adjusted = await client.post(
        f"/v1/recipes/{recipe['id']}/adjustments",
        json={
            "base_version": 1,
            "variable": "brew_time_s",
            "to_value": 180,
            "reason": "延长总时长。",
        },
    )
    assert adjusted.status_code == 201, adjusted.text
    v2 = adjusted.json()["recipe"]
    assert v2["variables"]["brew_time_s"] == 180
    assert "总时长 180 秒" in v2["steps"][0]["instruction"]
    assert "总时长 2 分 30 秒" not in v2["steps"][0]["instruction"]

    old = (await client.get(f"/v1/recipes/{recipe['id']}")).json()
    assert old["variables"]["brew_time_s"] == 150
    assert "总时长 2 分 30 秒" in old["steps"][0]["instruction"]

async def test_explicit_water_total_beats_stage_pours(client, monkeypatch):
    session, _ = await setup_coffee(
        client,
        monkeypatch,
        plan=_controlled_plan(
            "咖啡粉 15 g，闷蒸 30 g，注水至 100 g，注水至 150 g，"
            "总水量 225 g，水温 92 °C，总时长 150 秒。"
        ),
    )
    created = await client.post(
        f"/v1/sessions/{session['id']}/recipes",
        json={"base_plan_version": 1},
    )
    assert created.status_code == 201, created.text
    recipe = created.json()
    assert recipe["variables"]["dose_g"] == 15
    assert recipe["variables"]["water_g"] == 225
    assert recipe["variables"]["ratio"] == 15.0
    assert recipe["variables"]["water_temp_c"] == 92
    assert recipe["variables"]["brew_time_s"] == 150
    water = next(item for item in recipe["ingredients"] if item["name"] == "水")
    coffee = next(item for item in recipe["ingredients"] if item["name"] == "咖啡豆")
    assert water["amount"] == 225
    assert coffee["amount"] == 15
    assert "总水量 225 g" in recipe["steps"][0]["instruction"]

    total_first_session, _ = await setup_coffee(
        client,
        monkeypatch,
        plan=_controlled_plan(
            "咖啡粉 15 g，总水量 225 g，闷蒸 30 g，注水至 100 g，注水至 150 g，"
            "水温 92 °C，总时长 150 秒。"
        ),
    )
    total_first = await client.post(
        f"/v1/sessions/{total_first_session['id']}/recipes",
        json={"base_plan_version": 1},
    )
    assert total_first.status_code == 201, total_first.text
    assert total_first.json()["variables"]["water_g"] == 225


async def test_water_total_rejects_ambiguous_stages_without_explicit_total(
    client,
    monkeypatch,
):
    staged_session, _ = await setup_coffee(
        client,
        monkeypatch,
        plan=_controlled_plan(
            "咖啡粉 15 g，注水至 100 g，注水至 150 g，水温 92 °C，总时长 150 秒。"
        ),
    )
    staged = await client.post(
        f"/v1/sessions/{staged_session['id']}/recipes",
        json={"base_plan_version": 1},
    )
    assert staged.status_code == 422
    staged_error = staged.json()["error"]["details"]
    assert staged_error["reason"] == "water_total_ambiguous"
    assert staged_error["source"] == "terminal_pour"
    assert (await client.get(f"/v1/sessions/{staged_session['id']}/recipes")).json() == []

    local_session, _ = await setup_coffee(
        client,
        monkeypatch,
        plan=_controlled_plan(
            "咖啡粉 15 g，闷蒸 30 g，水温 92 °C，总时长 150 秒。"
        ),
    )
    local = await client.post(
        f"/v1/sessions/{local_session['id']}/recipes",
        json={"base_plan_version": 1},
    )
    assert local.status_code == 422
    local_error = local.json()["error"]["details"]
    assert local_error["reason"] == "water_total_ambiguous"
    assert local_error["source"] == "local_only"
    assert (await client.get(f"/v1/sessions/{local_session['id']}/recipes")).json() == []


async def test_colon_total_time_wins_and_only_total_is_rewritten(client, monkeypatch):
    session, _ = await setup_coffee(
        client,
        monkeypatch,
        plan=_controlled_plan(
            "咖啡粉 15 g，水 225 g，水温 92 °C，总时长：150 秒，闷蒸用时 30 秒。"
        ),
    )
    recipe = (
        await client.post(
            f"/v1/sessions/{session['id']}/recipes",
            json={"base_plan_version": 1},
        )
    ).json()
    assert recipe["variables"]["brew_time_s"] == 150
    instruction = recipe["steps"][0]["instruction"]
    assert "总时长：150 秒" in instruction
    assert "闷蒸用时 30 秒" in instruction

    adjusted = await client.post(
        f"/v1/recipes/{recipe['id']}/adjustments",
        json={
            "base_version": 1,
            "variable": "brew_time_s",
            "to_value": 180,
            "reason": "只延长总时长。",
        },
    )
    assert adjusted.status_code == 201, adjusted.text
    v2 = adjusted.json()["recipe"]
    assert v2["variables"]["brew_time_s"] == 180
    assert v2["variables"]["dose_g"] == 15
    assert v2["variables"]["water_g"] == 225
    assert v2["variables"]["water_temp_c"] == 92
    v2_instruction = v2["steps"][0]["instruction"]
    assert "总时长：180 秒" in v2_instruction
    assert "闷蒸用时 30 秒" in v2_instruction
    assert "总时长：150 秒" not in v2_instruction
    water = next(item for item in v2["ingredients"] if item["name"] == "水")
    coffee = next(item for item in v2["ingredients"] if item["name"] == "咖啡豆")
    assert water["amount"] == 225
    assert coffee["amount"] == 15

    old = (await client.get(f"/v1/recipes/{recipe['id']}")).json()
    assert old["variables"]["brew_time_s"] == 150
    assert "总时长：150 秒" in old["steps"][0]["instruction"]
    assert "闷蒸用时 30 秒" in old["steps"][0]["instruction"]
    assert [item["version"] for item in (await client.get(f"/v1/recipes/{v2['id']}/history")).json()] == [1, 2]

    ambiguous_session, _ = await setup_coffee(
        client,
        monkeypatch,
        plan=_controlled_plan(
            "咖啡粉 15 g，水 225 g，水温 92 °C，总时长 150 秒，备用总时长 180 秒。"
        ),
    )
    ambiguous = await client.post(
        f"/v1/sessions/{ambiguous_session['id']}/recipes",
        json={"base_plan_version": 1},
    )
    assert ambiguous.status_code == 422
    assert ambiguous.json()["error"]["details"]["reason"] == "brew_time_ambiguous"
    assert (await client.get(f"/v1/sessions/{ambiguous_session['id']}/recipes")).json() == []

async def test_water_total_label_rewrites_only_total_and_keeps_stage_pours(
    client,
    monkeypatch,
):
    session, _ = await setup_coffee(
        client,
        monkeypatch,
        plan=_controlled_plan(
            "咖啡粉 15 g，闷蒸 30 g，注水至 100 g，注水总量：225 g，"
            "水温 92 °C，总时长 150 秒。"
        ),
    )
    recipe = (
        await client.post(
            f"/v1/sessions/{session['id']}/recipes",
            json={"base_plan_version": 1},
        )
    ).json()
    assert recipe["variables"]["water_g"] == 225
    assert recipe["variables"]["ratio"] == 15.0
    assert "注水总量：225 g" in recipe["steps"][0]["instruction"]

    adjusted = await client.post(
        f"/v1/recipes/{recipe['id']}/adjustments",
        json={
            "base_version": 1,
            "variable": "water_g",
            "to_value": 240,
            "reason": "只调整总水量。",
        },
    )
    assert adjusted.status_code == 201, adjusted.text
    v2 = adjusted.json()["recipe"]
    assert v2["variables"]["water_g"] == 240
    assert v2["variables"]["dose_g"] == 15
    assert v2["variables"]["ratio"] == 16.0
    water = next(item for item in v2["ingredients"] if item["name"] == "水")
    coffee = next(item for item in v2["ingredients"] if item["name"] == "咖啡豆")
    assert water["amount"] == 240
    assert coffee["amount"] == 15
    instruction = v2["steps"][0]["instruction"]
    assert "注水总量：240 g" in instruction
    assert "注水至 100 g" in instruction
    assert "闷蒸 30 g" in instruction
    assert "225 g" not in instruction

    old = (await client.get(f"/v1/recipes/{recipe['id']}")).json()
    assert old["variables"]["water_g"] == 225
    assert "注水总量：225 g" in old["steps"][0]["instruction"]
    assert "注水至 100 g" in old["steps"][0]["instruction"]
    assert [item["version"] for item in (await client.get(f"/v1/recipes/{v2['id']}/history")).json()] == [1, 2]


async def test_total_time_rewrite_keeps_rest_duration_and_step_time(client, monkeypatch):
    session, _ = await setup_coffee(
        client,
        monkeypatch,
        plan=_controlled_plan(
            "咖啡粉 15 g，水 225 g，水温 92 °C，总时长：150 秒，静置时长 150 秒。"
        ),
    )
    recipe = (
        await client.post(
            f"/v1/sessions/{session['id']}/recipes",
            json={"base_plan_version": 1},
        )
    ).json()
    assert recipe["variables"]["brew_time_s"] == 150
    instruction = recipe["steps"][0]["instruction"]
    assert "总时长：150 秒" in instruction
    assert "静置时长 150 秒" in instruction

    adjusted = await client.post(
        f"/v1/recipes/{recipe['id']}/adjustments",
        json={
            "base_version": 1,
            "variable": "brew_time_s",
            "to_value": 180,
            "reason": "只调整总时长。",
        },
    )
    assert adjusted.status_code == 201, adjusted.text
    v2 = adjusted.json()["recipe"]
    assert v2["variables"]["brew_time_s"] == 180
    assert v2["variables"]["dose_g"] == 15
    assert v2["variables"]["water_g"] == 225
    v2_instruction = v2["steps"][0]["instruction"]
    assert "总时长：180 秒" in v2_instruction
    assert "静置时长 150 秒" in v2_instruction
    assert "总时长：150 秒" not in v2_instruction
    water = next(item for item in v2["ingredients"] if item["name"] == "水")
    coffee = next(item for item in v2["ingredients"] if item["name"] == "咖啡豆")
    assert water["amount"] == 225
    assert coffee["amount"] == 15

    old = (await client.get(f"/v1/recipes/{recipe['id']}")).json()
    assert old["variables"]["brew_time_s"] == 150
    assert "总时长：150 秒" in old["steps"][0]["instruction"]
    assert "静置时长 150 秒" in old["steps"][0]["instruction"]
    assert [item["version"] for item in (await client.get(f"/v1/recipes/{v2['id']}/history")).json()] == [1, 2]

async def test_inline_water_pour_source_is_located_once_for_adjustment(
    client,
    monkeypatch,
):
    session, _ = await setup_coffee(
        client,
        monkeypatch,
        plan=_controlled_plan("咖啡粉 15 g，注水 225 g，水温 92 °C，总时长 150 秒。"),
    )
    recipe = (
        await client.post(
            f"/v1/sessions/{session['id']}/recipes",
            json={"base_plan_version": 1},
        )
    ).json()
    assert recipe["variables"]["water_g"] == 225
    assert recipe["variables"]["ratio"] == 15.0
    assert "注水 225 g" in recipe["steps"][0]["instruction"]

    adjusted = await client.post(
        f"/v1/recipes/{recipe['id']}/adjustments",
        json={
            "base_version": 1,
            "variable": "water_g",
            "to_value": 240,
            "reason": "只调整总水量。",
        },
    )
    assert adjusted.status_code == 201, adjusted.text
    v2 = adjusted.json()["recipe"]
    assert v2["variables"]["water_g"] == 240
    assert v2["variables"]["dose_g"] == 15
    assert v2["variables"]["ratio"] == 16.0
    water = next(item for item in v2["ingredients"] if item["name"] == "水")
    coffee = next(item for item in v2["ingredients"] if item["name"] == "咖啡豆")
    assert water["amount"] == 240
    assert coffee["amount"] == 15
    assert "注水 240 g" in v2["steps"][0]["instruction"]
    assert "225 g" not in v2["steps"][0]["instruction"]

    old = (await client.get(f"/v1/recipes/{recipe['id']}")).json()
    assert old["variables"]["water_g"] == 225
    assert "注水 225 g" in old["steps"][0]["instruction"]
    assert [item["version"] for item in (await client.get(f"/v1/recipes/{v2['id']}/history")).json()] == [1, 2]


async def test_total_time_source_is_located_across_steps(client, monkeypatch):
    plan = _controlled_plan(
        "咖啡粉 15 g，水 225 g，水温 92 °C，总时长：150 秒。"
    )
    plan["steps"][1]["instruction"] = "等待片刻；萃取用时 150 秒。"
    session, _ = await setup_coffee(client, monkeypatch, plan=plan)
    recipe = (
        await client.post(
            f"/v1/sessions/{session['id']}/recipes",
            json={"base_plan_version": 1},
        )
    ).json()
    assert recipe["variables"]["brew_time_s"] == 150
    assert "总时长：150 秒" in recipe["steps"][0]["instruction"]
    assert "萃取用时 150 秒" in recipe["steps"][1]["instruction"]

    adjusted = await client.post(
        f"/v1/recipes/{recipe['id']}/adjustments",
        json={
            "base_version": 1,
            "variable": "brew_time_s",
            "to_value": 180,
            "reason": "只调整总时长。",
        },
    )
    assert adjusted.status_code == 201, adjusted.text
    v2 = adjusted.json()["recipe"]
    assert v2["variables"]["brew_time_s"] == 180
    assert v2["variables"]["water_g"] == 225
    assert "总时长：180 秒" in v2["steps"][0]["instruction"]
    assert "萃取用时 150 秒" in v2["steps"][1]["instruction"]
    assert "总时长：150 秒" not in v2["steps"][0]["instruction"]
    water = next(item for item in v2["ingredients"] if item["name"] == "水")
    coffee = next(item for item in v2["ingredients"] if item["name"] == "咖啡豆")
    assert water["amount"] == 225
    assert coffee["amount"] == 15

    old = (await client.get(f"/v1/recipes/{recipe['id']}")).json()
    assert old["variables"]["brew_time_s"] == 150
    assert "总时长：150 秒" in old["steps"][0]["instruction"]
    assert "萃取用时 150 秒" in old["steps"][1]["instruction"]
    assert [item["version"] for item in (await client.get(f"/v1/recipes/{v2['id']}/history")).json()] == [1, 2]


async def test_stop_condition_and_total_water_update_together(client, monkeypatch):
    plan = _controlled_plan(
        "咖啡粉 15 g，总水量 225 g，中途注水至 100 g，"
        "最后继续注水至 225 g 后停止，水温 92 °C，总时长 150 秒。"
    )
    plan["steps"][0]["completion_criteria"] = ["继续注水至 225 g 后停止"]
    session, _ = await setup_coffee(client, monkeypatch, plan=plan)
    recipe = (
        await client.post(
            f"/v1/sessions/{session['id']}/recipes",
            json={"base_plan_version": 1},
        )
    ).json()
    assert recipe["variables"]["water_g"] == 225
    assert "总水量 225 g" in recipe["steps"][0]["instruction"]
    assert "中途注水至 100 g" in recipe["steps"][0]["instruction"]
    assert "继续注水至 225 g 后停止" in recipe["steps"][0]["instruction"]
    assert "继续注水至 225 g 后停止" in recipe["steps"][0]["target"]

    adjusted = await client.post(
        f"/v1/recipes/{recipe['id']}/adjustments",
        json={
            "base_version": 1,
            "variable": "water_g",
            "to_value": 240,
            "reason": "只调整总水量。",
        },
    )
    assert adjusted.status_code == 201, adjusted.text
    v2 = adjusted.json()["recipe"]
    assert v2["variables"]["water_g"] == 240
    assert v2["variables"]["ratio"] == 16.0
    water = next(item for item in v2["ingredients"] if item["name"] == "水")
    assert water["amount"] == 240
    instruction = v2["steps"][0]["instruction"]
    assert "总水量 240 g" in instruction
    assert "中途注水至 100 g" in instruction
    assert "继续注水至 240 g 后停止" in instruction
    assert "继续注水至 240 g 后停止" in v2["steps"][0]["target"]
    assert "225 g" not in instruction

    old = (await client.get(f"/v1/recipes/{recipe['id']}")).json()
    assert old["variables"]["water_g"] == 225
    assert "总水量 225 g" in old["steps"][0]["instruction"]
    assert "中途注水至 100 g" in old["steps"][0]["instruction"]
    assert "继续注水至 225 g 后停止" in old["steps"][0]["target"]
    assert [item["version"] for item in (await client.get(f"/v1/recipes/{v2['id']}/history")).json()] == [1, 2]


async def test_creation_prompts_when_total_sources_are_only_in_summary(
    client,
    monkeypatch,
):
    water_plan = _controlled_plan("咖啡粉 15 g，水温 92 °C，总时长 150 秒。")
    water_plan["summary"] = "总水量 225 g。"
    water_session, _ = await setup_coffee(client, monkeypatch, plan=water_plan)
    water_created = await client.post(
        f"/v1/sessions/{water_session['id']}/recipes",
        json={"base_plan_version": 1},
    )
    assert water_created.status_code == 422
    water_error = water_created.json()["error"]
    assert water_error["details"]["reason"] == "total_source_unconfirmed"
    assert water_error["details"]["variable"] == "water_g"
    assert "摘要" in water_error["message"]
    assert (await client.get(f"/v1/sessions/{water_session['id']}/recipes")).json() == []

    time_plan = _controlled_plan("咖啡粉 15 g，水 225 g，水温 92 °C。")
    time_plan["summary"] = "总时长 150 秒。"
    time_session, _ = await setup_coffee(client, monkeypatch, plan=time_plan)
    time_created = await client.post(
        f"/v1/sessions/{time_session['id']}/recipes",
        json={"base_plan_version": 1},
    )
    assert time_created.status_code == 422
    time_error = time_created.json()["error"]
    assert time_error["details"]["reason"] == "total_source_unconfirmed"
    assert time_error["details"]["variable"] == "brew_time_s"
    assert (await client.get(f"/v1/sessions/{time_session['id']}/recipes")).json() == []


async def test_legacy_recipe_without_step_source_still_returns_422(client):
    service = client.app.state.recipe_service
    steps = [
        {
            "id": "rst_1",
            "order": 1,
            "instruction": "咖啡粉 15 g，水温 92 °C，总时长 150 秒。",
            "duration_s": 60,
            "target": "按步骤完成。",
        }
    ]
    with pytest.raises(ApiError) as error:
        service._locate_water_spans(steps, 225)
    assert error.value.status_code == 422
    assert error.value.details["reason"] == "total_source_unconfirmed"
    assert error.value.details["variable"] == "water_g"

async def test_lowering_total_below_intermediate_pour_is_rejected(client, monkeypatch):
    plan = _controlled_plan(
        "咖啡粉 15 g，总水量 225 g，中途注水至 100 g，"
        "最后继续注水至 225 g 后停止，水温 92 °C，总时长 150 秒。"
    )
    plan["steps"][0]["completion_criteria"] = ["继续注水至 225 g 后停止"]
    session, _ = await setup_coffee(client, monkeypatch, plan=plan)
    recipe = (
        await client.post(
            f"/v1/sessions/{session['id']}/recipes",
            json={"base_plan_version": 1},
        )
    ).json()
    assert recipe["variables"]["water_g"] == 225
    assert "中途注水至 100 g" in recipe["steps"][0]["instruction"]
    assert "继续注水至 225 g 后停止" in recipe["steps"][0]["target"]

    rejected = await client.post(
        f"/v1/recipes/{recipe['id']}/adjustments",
        json={
            "base_version": 1,
            "variable": "water_g",
            "to_value": 90,
            "reason": "尝试低于中途注水量。",
        },
    )
    assert rejected.status_code == 422
    details = rejected.json()["error"]["details"]
    assert details["reason"] == "intermediate_water_exceeds_total"
    assert details["water_g"] == 90
    assert details["intermediate_targets"] == [100]
    recipes = (await client.get(f"/v1/sessions/{session['id']}/recipes")).json()
    assert [item["version"] for item in recipes] == [1]
    assert [item["version"] for item in (await client.get(f"/v1/recipes/{recipe['id']}/history")).json()] == [1]
    old = (await client.get(f"/v1/recipes/{recipe['id']}")).json()
    assert old["variables"]["water_g"] == 225
    assert "中途注水至 100 g" in old["steps"][0]["instruction"]
    assert "继续注水至 225 g 后停止" in old["steps"][0]["target"]

    allowed = await client.post(
        f"/v1/recipes/{recipe['id']}/adjustments",
        json={
            "base_version": 1,
            "variable": "water_g",
            "to_value": 240,
            "reason": "提高到中途注水量之上。",
        },
    )
    assert allowed.status_code == 201, allowed.text
    v2 = allowed.json()["recipe"]
    assert v2["variables"]["water_g"] == 240
    assert v2["variables"]["ratio"] == 16.0
    water = next(item for item in v2["ingredients"] if item["name"] == "水")
    assert water["amount"] == 240
    instruction = v2["steps"][0]["instruction"]
    assert "总水量 240 g" in instruction
    assert "中途注水至 100 g" in instruction
    assert "继续注水至 240 g 后停止" in instruction
    assert "继续注水至 240 g 后停止" in v2["steps"][0]["target"]
    old = (await client.get(f"/v1/recipes/{recipe['id']}")).json()
    assert old["variables"]["water_g"] == 225
    assert [item["version"] for item in (await client.get(f"/v1/recipes/{v2['id']}/history")).json()] == [1, 2]

async def test_sequential_water_adjustments_keep_intermediate_target(
    client,
    monkeypatch,
):
    plan = _controlled_plan(
        "咖啡粉 15 g，总水量 225 g，中途注水至 100 g，"
        "最后继续注水至 225 g 后停止，水温 92 °C，总时长 150 秒。"
    )
    plan["steps"][0]["completion_criteria"] = ["继续注水至 225 g 后停止"]
    session, _ = await setup_coffee(client, monkeypatch, plan=plan)
    recipe = (
        await client.post(
            f"/v1/sessions/{session['id']}/recipes",
            json={"base_plan_version": 1},
        )
    ).json()
    assert recipe["variables"]["water_g"] == 225

    first = await client.post(
        f"/v1/recipes/{recipe['id']}/adjustments",
        json={
            "base_version": 1,
            "variable": "water_g",
            "to_value": 100,
            "reason": "先降到中途注水量。",
        },
    )
    assert first.status_code == 201, first.text
    v2 = first.json()["recipe"]
    assert v2["variables"]["water_g"] == 100
    assert v2["variables"]["ratio"] == 6.67
    instruction_v2 = v2["steps"][0]["instruction"]
    assert "总水量 100 g" in instruction_v2
    assert "中途注水至 100 g" in instruction_v2
    assert "继续注水至 100 g 后停止" in instruction_v2
    assert "继续注水至 100 g 后停止" in v2["steps"][0]["target"]

    second = await client.post(
        f"/v1/recipes/{v2['id']}/adjustments",
        json={
            "base_version": 2,
            "variable": "water_g",
            "to_value": 240,
            "reason": "再从 100 提高到 240。",
        },
    )
    assert second.status_code == 201, second.text
    v3 = second.json()["recipe"]
    assert v3["variables"]["water_g"] == 240
    assert v3["variables"]["ratio"] == 16.0
    water = next(item for item in v3["ingredients"] if item["name"] == "水")
    assert water["amount"] == 240
    instruction_v3 = v3["steps"][0]["instruction"]
    assert "总水量 240 g" in instruction_v3
    assert "中途注水至 100 g" in instruction_v3
    assert "继续注水至 240 g 后停止" in instruction_v3
    assert "继续注水至 240 g 后停止" in v3["steps"][0]["target"]

    history = (await client.get(f"/v1/recipes/{v3['id']}/history")).json()
    assert [item["version"] for item in history] == [1, 2, 3]
    v1 = (await client.get(f"/v1/recipes/{recipe['id']}")).json()
    assert v1["variables"]["water_g"] == 225
    assert "中途注水至 100 g" in v1["steps"][0]["instruction"]
    assert "继续注水至 225 g 后停止" in v1["steps"][0]["target"]
    v2_get = (await client.get(f"/v1/recipes/{v2['id']}")).json()
    assert v2_get["variables"]["water_g"] == 100
    assert "中途注水至 100 g" in v2_get["steps"][0]["instruction"]
    assert "继续注水至 100 g 后停止" in v2_get["steps"][0]["target"]

async def test_marks_keep_continue_pour_as_intermediate_target(client, monkeypatch):
    plan = _controlled_plan(
        "咖啡粉 15 g，总水量 225 g，闷蒸后继续注水至 100 g，等待 10 秒，"
        "水温 92 °C，总时长 150 秒。"
    )
    plan["steps"][0]["completion_criteria"] = ["注水至 225 g 后停止"]
    session, _ = await setup_coffee(client, monkeypatch, plan=plan)
    recipe = (
        await client.post(
            f"/v1/sessions/{session['id']}/recipes",
            json={"base_plan_version": 1},
        )
    ).json()
    assert recipe["variables"]["water_g"] == 225
    assert "继续注水至 100 g" in recipe["steps"][0]["instruction"]
    assert "注水至 225 g 后停止" in recipe["steps"][0]["target"]

    rejected = await client.post(
        f"/v1/recipes/{recipe['id']}/adjustments",
        json={
            "base_version": 1,
            "variable": "water_g",
            "to_value": 90,
            "reason": "低于中途注水量。",
        },
    )
    assert rejected.status_code == 422
    assert (
        rejected.json()["error"]["details"]["reason"]
        == "intermediate_water_exceeds_total"
    )

    first = await client.post(
        f"/v1/recipes/{recipe['id']}/adjustments",
        json={
            "base_version": 1,
            "variable": "water_g",
            "to_value": 100,
            "reason": "先降到与中途相同。",
        },
    )
    assert first.status_code == 201, first.text
    v2 = first.json()["recipe"]
    assert v2["variables"]["water_g"] == 100
    v2_instruction = v2["steps"][0]["instruction"]
    assert "总水量 100 g" in v2_instruction
    assert "继续注水至 100 g" in v2_instruction
    assert "等待 10 秒" in v2_instruction
    assert "注水至 100 g 后停止" in v2["steps"][0]["target"]

    second = await client.post(
        f"/v1/recipes/{v2['id']}/adjustments",
        json={
            "base_version": 2,
            "variable": "water_g",
            "to_value": 240,
            "reason": "再升到 240。",
        },
    )
    assert second.status_code == 201, second.text
    v3 = second.json()["recipe"]
    assert v3["variables"]["water_g"] == 240
    assert v3["variables"]["ratio"] == 16.0
    water = next(item for item in v3["ingredients"] if item["name"] == "水")
    assert water["amount"] == 240
    v3_instruction = v3["steps"][0]["instruction"]
    assert "总水量 240 g" in v3_instruction
    assert "继续注水至 100 g" in v3_instruction
    assert "等待 10 秒" in v3_instruction
    assert "注水至 240 g 后停止" in v3["steps"][0]["target"]

    history = (await client.get(f"/v1/recipes/{v3['id']}/history")).json()
    assert [item["version"] for item in history] == [1, 2, 3]
    v1 = (await client.get(f"/v1/recipes/{recipe['id']}")).json()
    assert v1["variables"]["water_g"] == 225
    assert "继续注水至 100 g" in v1["steps"][0]["instruction"]
    assert "注水至 225 g 后停止" in v1["steps"][0]["target"]
    v2_get = (await client.get(f"/v1/recipes/{v2['id']}")).json()
    assert v2_get["variables"]["water_g"] == 100
    assert "继续注水至 100 g" in v2_get["steps"][0]["instruction"]
    assert "注水至 100 g 后停止" in v2_get["steps"][0]["target"]


async def test_adjustment_without_source_marks_requires_confirmation(client):
    service = client.app.state.recipe_service
    steps = [
        {
            "instruction": "总水量 225 g，闷蒸后继续注水至 100 g。",
            "target": "注水至 225 g 后停止。",
        }
    ]
    with pytest.raises(ApiError) as error:
        service._rewrite_steps(
            steps,
            {"water_g": 225},
            {"water_g": 240},
            None,
        )
    assert error.value.status_code == 422
    assert error.value.details["reason"] == "total_source_unconfirmed"
    assert error.value.details["variable"] == "water_g"

async def test_total_water_and_last_pour_instruction_update_together(
    client,
    monkeypatch,
):
    plan = _controlled_plan(
        "咖啡粉 15 g，总水量 225 g，分两次注水至 225 g，等滤杯滴完，"
        "水温 92 °C，总时长 150 秒。"
    )
    session, _ = await setup_coffee(client, monkeypatch, plan=plan)
    recipe = (
        await client.post(
            f"/v1/sessions/{session['id']}/recipes",
            json={"base_plan_version": 1},
        )
    ).json()
    assert recipe["variables"]["water_g"] == 225
    assert "分两次注水至 225 g" in recipe["steps"][0]["instruction"]
    assert "等滤杯滴完" in recipe["steps"][0]["instruction"]

    adjusted = await client.post(
        f"/v1/recipes/{recipe['id']}/adjustments",
        json={
            "base_version": 1,
            "variable": "water_g",
            "to_value": 240,
            "reason": "调整总水量。",
        },
    )
    assert adjusted.status_code == 201, adjusted.text
    v2 = adjusted.json()["recipe"]
    assert v2["variables"]["water_g"] == 240
    assert v2["variables"]["ratio"] == 16.0
    water = next(item for item in v2["ingredients"] if item["name"] == "水")
    assert water["amount"] == 240
    instruction = v2["steps"][0]["instruction"]
    assert "总水量 240 g" in instruction
    assert "分两次注水至 240 g" in instruction
    assert "等滤杯滴完" in instruction
    old = (await client.get(f"/v1/recipes/{recipe['id']}")).json()
    assert old["variables"]["water_g"] == 225
    assert "分两次注水至 225 g" in old["steps"][0]["instruction"]


async def test_legacy_recipe_without_marks_recovers_on_first_adjustment(
    client,
    monkeypatch,
):
    plan = _controlled_plan(
        "咖啡粉 15 g，总水量 225 g，分两次注水至 225 g，等滤杯滴完，"
        "水温 92 °C，总时长 150 秒。"
    )
    session, _ = await setup_coffee(client, monkeypatch, plan=plan)
    recipe = (
        await client.post(
            f"/v1/sessions/{session['id']}/recipes",
            json={"base_plan_version": 1},
        )
    ).json()
    store = client.app.state.recipe_service.store
    stored = await store.find_recipe(recipe["id"])
    stored.pop("total_sources", None)
    await store.save_recipe(stored)

    adjusted = await client.post(
        f"/v1/recipes/{recipe['id']}/adjustments",
        json={
            "base_version": 1,
            "variable": "water_g",
            "to_value": 240,
            "reason": "旧配方首次调整。",
        },
    )
    assert adjusted.status_code == 201, adjusted.text
    v2 = adjusted.json()["recipe"]
    assert v2["variables"]["water_g"] == 240
    assert v2["total_sources"] is not None
    assert "分两次注水至 240 g" in v2["steps"][0]["instruction"]
    water = next(item for item in v2["ingredients"] if item["name"] == "水")
    assert water["amount"] == 240
    old = (await client.get(f"/v1/recipes/{recipe['id']}")).json()
    assert old["variables"]["water_g"] == 225
    assert old["steps"][0]["instruction"].find("分两次注水至 225 g") >= 0
    assert [item["version"] for item in (await client.get(f"/v1/recipes/{v2['id']}/history")).json()] == [1, 2]


async def test_legacy_ambiguous_source_offers_confirmation(client, monkeypatch):
    plan = _controlled_plan(
        "咖啡粉 15 g，总水量 225 g，分两次注水至 225 g，等滤杯滴完，"
        "水温 92 °C，总时长 150 秒。"
    )
    session, _ = await setup_coffee(client, monkeypatch, plan=plan)
    recipe = (
        await client.post(
            f"/v1/sessions/{session['id']}/recipes",
            json={"base_plan_version": 1},
        )
    ).json()
    store = client.app.state.recipe_service.store
    stored = await store.find_recipe(recipe["id"])
    stored.pop("total_sources", None)
    stored["steps"][0]["instruction"] = (
        "咖啡粉 15 g，总水量 225 g，注水至 100 g，继续注水至 225 g，"
        "等待 10 秒，水温 92 °C，总时长 150 秒。"
    )
    stored["steps"][0]["target"] = "注水至 225 g，等滤杯滴完。"
    await store.save_recipe(stored)

    rejected = await client.post(
        f"/v1/recipes/{recipe['id']}/adjustments",
        json={
            "base_version": 1,
            "variable": "water_g",
            "to_value": 240,
            "reason": "旧配方来源不明确。",
        },
    )
    assert rejected.status_code == 422
    details = rejected.json()["error"]["details"]
    assert details["reason"] == "total_source_unconfirmed"
    assert details["confirmation_required"] is True
    assert details["confirm_field"] == "water_source_confirmation"
    candidates = details["candidates"]
    declaration_id = next(
        item["candidate_id"]
        for item in candidates
        if item["kind"] == "explicit"
    )
    final_id = next(
        item["candidate_id"]
        for item in candidates
        if item["kind"] == "terminal" and item["field"] == "target"
    )
    assert details.get("requires_final") is True

    incomplete = await client.post(
        f"/v1/recipes/{recipe['id']}/adjustments",
        json={
            "base_version": 1,
            "variable": "water_g",
            "to_value": 240,
            "reason": "只选声明。",
            "water_source_confirmation": {
                "declaration": [declaration_id],
            },
        },
    )
    assert incomplete.status_code == 422
    incomplete_details = incomplete.json()["error"]["details"]
    assert incomplete_details["reason"] == "invalid_water_source_confirmation"
    assert "final" in incomplete_details["missing"]
    assert incomplete_details["requires_final"] is True
    assert [item["version"] for item in (await client.get(f"/v1/sessions/{session['id']}/recipes")).json()] == [1]

    invalid_role = await client.post(
        f"/v1/recipes/{recipe['id']}/adjustments",
        json={
            "base_version": 1,
            "variable": "water_g",
            "to_value": 240,
            "reason": "最终指令角色错误。",
            "water_source_confirmation": {
                "declaration": [declaration_id],
                "final": [declaration_id],
            },
        },
    )
    assert invalid_role.status_code == 422
    invalid_details = invalid_role.json()["error"]["details"]
    assert invalid_details["reason"] == "invalid_water_source_confirmation"
    assert declaration_id in invalid_details["invalid"]
    assert [item["version"] for item in (await client.get(f"/v1/sessions/{session['id']}/recipes")).json()] == [1]

    bad_type = await client.post(
        f"/v1/recipes/{recipe['id']}/adjustments",
        json={
            "base_version": 1,
            "variable": "water_g",
            "to_value": 240,
            "reason": "候选类型错误。",
            "water_source_confirmation": {
                "declaration": ["0"],
            },
        },
    )
    assert bad_type.status_code == 422
    assert [item["version"] for item in (await client.get(f"/v1/sessions/{session['id']}/recipes")).json()] == [1]

    confirmed = await client.post(
        f"/v1/recipes/{recipe['id']}/adjustments",
        json={
            "base_version": 1,
            "variable": "water_g",
            "to_value": 240,
            "reason": "用户确认来源后调整。",
            "water_source_confirmation": {
                "declaration": [declaration_id],
                "final": [final_id],
            },
        },
    )
    assert confirmed.status_code == 201, confirmed.text
    v2 = confirmed.json()["recipe"]
    assert v2["variables"]["water_g"] == 240
    assert v2["total_sources"] is not None
    v2_instruction = v2["steps"][0]["instruction"]
    assert "总水量 240 g" in v2_instruction
    assert "注水至 100 g" in v2_instruction
    assert "继续注水至 225 g" in v2_instruction
    assert "注水至 240 g，等滤杯滴完" in v2["steps"][0]["target"]
    water = next(item for item in v2["ingredients"] if item["name"] == "水")
    assert water["amount"] == 240
    old = (await client.get(f"/v1/recipes/{recipe['id']}")).json()
    assert old["variables"]["water_g"] == 225
    assert "总水量 225 g" in old["steps"][0]["instruction"]
    assert "注水至 100 g" in old["steps"][0]["instruction"]
    assert [item["version"] for item in (await client.get(f"/v1/recipes/{v2['id']}/history")).json()] == [1, 2]

async def test_mid_step_completion_condition_is_not_final_stop(
    client,
    monkeypatch,
):
    plan = _controlled_plan(
        "咖啡粉 15 g，总水量 225 g，水温 92 °C，总时长 150 秒。"
    )
    plan["steps"][0]["completion_criteria"] = ["注水至 100 g"]
    plan["steps"][1]["instruction"] = "等待 10 秒。"
    plan["steps"][1]["completion_criteria"] = ["注水至 225 g 后停止"]
    session, _ = await setup_coffee(client, monkeypatch, plan=plan)
    recipe = (
        await client.post(
            f"/v1/sessions/{session['id']}/recipes",
            json={"base_plan_version": 1},
        )
    ).json()
    assert recipe["variables"]["water_g"] == 225
    assert "注水至 100 g" in recipe["steps"][0]["target"]
    assert "注水至 225 g 后停止" in recipe["steps"][1]["target"]

    adjusted = await client.post(
        f"/v1/recipes/{recipe['id']}/adjustments",
        json={
            "base_version": 1,
            "variable": "water_g",
            "to_value": 240,
            "reason": "只调整总水量。",
        },
    )
    assert adjusted.status_code == 201, adjusted.text
    v2 = adjusted.json()["recipe"]
    assert v2["variables"]["water_g"] == 240
    assert "注水至 100 g" in v2["steps"][0]["target"]
    assert "注水至 240 g 后停止" in v2["steps"][1]["target"]
    water = next(item for item in v2["ingredients"] if item["name"] == "水")
    assert water["amount"] == 240
    old = (await client.get(f"/v1/recipes/{recipe['id']}")).json()
    assert old["variables"]["water_g"] == 225
    assert "注水至 225 g 后停止" in old["steps"][1]["target"]


async def test_conflicting_total_and_final_stop_is_rejected(client, monkeypatch):
    plan = _controlled_plan(
        "咖啡粉 15 g，总水量 225 g，最后注水至 220 g 后停止，"
        "水温 92 °C，总时长 150 秒。"
    )
    session, _ = await setup_coffee(client, monkeypatch, plan=plan)
    created = await client.post(
        f"/v1/sessions/{session['id']}/recipes",
        json={"base_plan_version": 1},
    )
    assert created.status_code == 422
    details = created.json()["error"]["details"]
    assert details["reason"] == "water_total_conflicts_with_final"
    assert details["water_g"] == 225
    assert details["final_targets"] == [220]
    assert (await client.get(f"/v1/sessions/{session['id']}/recipes")).json() == []


async def test_legacy_conflicting_final_stop_rejects_adjustment(
    client,
    monkeypatch,
):
    plan = _controlled_plan(
        "咖啡粉 15 g，总水量 225 g，分两次注水至 225 g，等滤杯滴完，"
        "水温 92 °C，总时长 150 秒。"
    )
    session, _ = await setup_coffee(client, monkeypatch, plan=plan)
    recipe = (
        await client.post(
            f"/v1/sessions/{session['id']}/recipes",
            json={"base_plan_version": 1},
        )
    ).json()
    store = client.app.state.recipe_service.store
    stored = await store.find_recipe(recipe["id"])
    stored.pop("total_sources", None)
    stored["steps"][0]["instruction"] = (
        "咖啡粉 15 g，总水量 225 g，最后注水至 220 g 后停止，"
        "水温 92 °C，总时长 150 秒。"
    )
    await store.save_recipe(stored)

    adjusted = await client.post(
        f"/v1/recipes/{recipe['id']}/adjustments",
        json={
            "base_version": 1,
            "variable": "water_g",
            "to_value": 240,
            "reason": "冲突旧配方。",
        },
    )
    assert adjusted.status_code == 422
    details = adjusted.json()["error"]["details"]
    assert details["reason"] == "water_total_conflicts_with_final"
    assert details["water_g"] == 225
    assert details["final_targets"] == [220]
    recipes = (await client.get(f"/v1/sessions/{session['id']}/recipes")).json()
    assert [item["version"] for item in recipes] == [1]
    old = (await client.get(f"/v1/recipes/{recipe['id']}")).json()
    assert old["variables"]["water_g"] == 225
