from __future__ import annotations

import copy

from test_progress import setup_plan

PHOTO_CONDITIONS = {
    "skill_level": "beginner",
    "stabilization": "handheld",
    "aspect_ratio": "9:16",
}


def photo_plan(visual_aid=None) -> dict:
    plan = {
        "title": "手机环绕拍一杯咖啡 8 秒",
        "summary": "布光、构图、环绕、回看。",
        "assumptions": ["使用手机广角镜头"],
        "preparation": [{"text": "把咖啡杯放在桌面中央。", "optional": False}],
        "steps": [
            {
                "phase": "prepare",
                "title": "布置光线与主体",
                "instruction": "把咖啡杯放在桌面中央，侧前方补光。",
                "why": "让主体和背景分离。",
                "duration_s": 180,
                "completion_criteria": ["杯口完整可见", "背景没有强反光"],
                "safety": ["注意桌面稳定"],
            },
            {
                "phase": "execute",
                "title": "环绕拍摄 8 秒",
                "instruction": "保持手机水平，从杯子的左侧缓慢绕到右侧，约 8 秒一圈。",
                "why": "让主体保持居中并获得环绕运动。",
                "duration_s": 30,
                "completion_criteria": ["主体始终在画面内", "运动速度均匀"],
                "safety": ["手稳，避免碰撞"],
            },
            {
                "phase": "verify",
                "title": "回看并确认起止",
                "instruction": "播放短片，检查开头和结尾各停留约 1 秒，画面没有突然抖动。",
                "why": "确认成片可用。",
                "duration_s": 120,
                "completion_criteria": ["短片有清楚起止", "没有明显突然抖动"],
                "safety": [],
            },
        ],
        "total_estimated_min": 15,
        "safety_notes": ["2D 文字说明不代表真实焦距与景深。"],
    }
    if visual_aid is not None:
        plan = copy.deepcopy(plan)
        plan["steps"][1]["visual_aid"] = visual_aid
    return plan


async def test_photography_missing_orbit_gets_structured_fallback(client, monkeypatch):
    session, plan = await setup_plan(
        client,
        monkeypatch,
        domain="photography",
        conditions=PHOTO_CONDITIONS,
        plan=photo_plan(),
    )
    assert plan["domain"] == "photography"
    camera = plan["steps"][1]["visual_aid"]["camera_move"]
    assert camera["shot_type"] == "orbit_cw"
    assert camera["duration_s"] == 8
    assert any("服务端按步骤文字生成" in note for note in plan["safety_notes"])
    assert any("device_model" in note for note in plan["assumptions"])
    assert any("lighting" in note for note in plan["assumptions"])
    assert any("运动" in note or "评分" in note for note in plan["safety_notes"])


async def test_photography_non_orbit_missing_spec_stays_clearly_missing(client, monkeypatch):
    plan_data = photo_plan()
    plan_data["steps"][1]["instruction"] = "保持机位不变，推近拍摄 8 秒。"
    plan_data["steps"][1]["title"] = "推近拍摄"
    session, plan = await setup_plan(
        client,
        monkeypatch,
        domain="photography",
        conditions=PHOTO_CONDITIONS,
        plan=plan_data,
    )
    assert all(step["visual_aid"] is None for step in plan["steps"])
    assert any("未提供合法运镜数据" in note for note in plan["safety_notes"])


async def test_photography_valid_camera_move_is_preserved(client, monkeypatch):
    visual = {
        "type": "camera_move",
        "camera_move": {
            "id": "cam_1",
            "shot_type": "orbit_cw",
            "motion_type": "camera_move",
            "technique": "handheld",
            "subject_anchor": {"x": 0.5, "y": 0.55, "label": "咖啡杯"},
            "position_path": {
                "space": "normalized_top_down",
                "start": {"x": 0.3, "y": 0.7},
                "end": {"x": 0.7, "y": 0.3},
                "control": None,
                "arc": "cw",
            },
            "orientation_path": None,
            "zoom": None,
            "duration_s": 8,
            "easing": "ease_in_out",
            "aspect_ratio": "9:16",
            "notes": ["主体保持在画面中央"],
            "limitations": ["2D 俯视示意，不代表真实焦距。"],
        },
    }
    session, plan = await setup_plan(
        client,
        monkeypatch,
        domain="photography",
        conditions=PHOTO_CONDITIONS,
        plan=photo_plan(visual),
    )
    step = plan["steps"][1]
    assert step["visual_aid"]["type"] == "camera_move"
    assert step["visual_aid"]["camera_move"]["duration_s"] == 8


async def test_photography_invalid_camera_move_is_replaced_by_structured_fallback(
    client,
    monkeypatch,
):
    session, plan = await setup_plan(
        client,
        monkeypatch,
        domain="photography",
        conditions=PHOTO_CONDITIONS,
        plan=photo_plan({"type": "camera_move", "camera_move": {"id": "bad"}}),
    )
    camera = plan["steps"][1]["visual_aid"]["camera_move"]
    assert camera["id"] == "cam_orbit"
    assert camera["shot_type"] == "orbit_cw"
    assert any("服务端按步骤文字生成" in note for note in plan["safety_notes"])
    assert plan["version"] == 1