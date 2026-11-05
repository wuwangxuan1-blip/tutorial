from __future__ import annotations

import copy

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
