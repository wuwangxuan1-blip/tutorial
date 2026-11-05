from __future__ import annotations

import copy

import pytest
from pydantic import ValidationError

from app.models.camera import CameraMoveSpec, validate_visual_aid


def valid_orbit() -> dict:
    return {
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
        "limitations": ["2D 俯视示意，不代表真实焦距、景深或精确轨迹。"],
    }


def valid_zoom() -> dict:
    return {
        "id": "cam_zoom",
        "shot_type": "zoom_in",
        "motion_type": "lens_zoom",
        "technique": "tripod",
        "subject_anchor": {"x": 0.5, "y": 0.5, "label": "杯口"},
        "position_path": None,
        "orientation_path": None,
        "zoom": {"start_scale": 1.0, "end_scale": 2.0},
        "duration_s": 4,
        "easing": "ease_in",
        "aspect_ratio": "16:9",
        "notes": [],
        "limitations": ["2D 取景框示意，不代表真实焦距。"],
    }


def test_valid_camera_move_specs_are_accepted():
    orbit = CameraMoveSpec.model_validate(valid_orbit())
    assert orbit.shot_type == "orbit_cw"
    assert orbit.position_path is not None
    zoom = CameraMoveSpec.model_validate(valid_zoom())
    assert zoom.zoom is not None
    assert validate_visual_aid({"type": "camera_move", "camera_move": valid_orbit()})[
        "camera_move"
    ]["duration_s"] == 8


@pytest.mark.parametrize(
    "mutate",
    [
        lambda spec: spec["position_path"]["start"].update({"x": float("nan")}),
        lambda spec: spec["position_path"]["end"].update({"y": 1.2}),
        lambda spec: spec.update({"position_path": None}),
        lambda spec: spec.update({"motion_type": "lens_zoom"}),
        lambda spec: spec["position_path"].update({"arc": "none"}),
        lambda spec: spec.update({"duration_s": 11}),
        lambda spec: spec.update({"easing": "bounce"}),
        lambda spec: spec.update({"limitations": ["没有说明平面示意局限。"]}),
        lambda spec: spec.update({"notes": ["x" * 201]}),
    ],
)
def test_invalid_orbit_specs_are_rejected(mutate):
    spec = copy.deepcopy(valid_orbit())
    mutate(spec)
    with pytest.raises(ValidationError):
        CameraMoveSpec.model_validate(spec)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda spec: spec.update({"position_path": valid_orbit()["position_path"]}),
        lambda spec: spec["zoom"].update({"start_scale": 2.0, "end_scale": 1.0}),
        lambda spec: spec.update({"shot_type": "zoom_out"}),
    ],
)
def test_invalid_zoom_specs_are_rejected(mutate):
    spec = copy.deepcopy(valid_zoom())
    mutate(spec)
    with pytest.raises(ValidationError):
        CameraMoveSpec.model_validate(spec)


def test_static_and_orientation_specs_reject_conflicts():
    static = {
        **valid_orbit(),
        "shot_type": "static",
        "motion_type": "static",
        "position_path": None,
        "orientation_path": None,
        "zoom": None,
    }
    assert CameraMoveSpec.model_validate(static).shot_type == "static"
    with pytest.raises(ValidationError):
        CameraMoveSpec.model_validate({**static, "position_path": valid_orbit()["position_path"]})

    orientation = {
        **valid_orbit(),
        "shot_type": "pan_left",
        "motion_type": "orientation_only",
        "position_path": None,
        "orientation_path": {
            "start_yaw_deg": -30,
            "end_yaw_deg": 30,
            "start_pitch_deg": 0,
            "end_pitch_deg": 0,
        },
        "zoom": None,
    }
    with pytest.raises(ValidationError):
        CameraMoveSpec.model_validate(orientation)