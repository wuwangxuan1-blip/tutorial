from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Point(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)


class SubjectAnchor(Point):
    label: str = Field(min_length=1, max_length=40)


class PositionPath(BaseModel):
    model_config = ConfigDict(extra="forbid")

    space: Literal["normalized_top_down"]
    start: Point
    end: Point
    control: Point | None = None
    arc: Literal["none", "cw", "ccw"] = "none"

    @model_validator(mode="after")
    def start_differs(self) -> "PositionPath":
        if self.start.x == self.end.x and self.start.y == self.end.y:
            raise ValueError("position_path start and end must differ")
        return self


class OrientationPath(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_yaw_deg: float = Field(ge=-180, le=180)
    end_yaw_deg: float = Field(ge=-180, le=180)
    start_pitch_deg: float = Field(ge=-90, le=90)
    end_pitch_deg: float = Field(ge=-90, le=90)

    @model_validator(mode="after")
    def orientation_differs(self) -> "OrientationPath":
        if (
            self.start_yaw_deg == self.end_yaw_deg
            and self.start_pitch_deg == self.end_pitch_deg
        ):
            raise ValueError("orientation_path must change yaw or pitch")
        return self


class ZoomSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_scale: float = Field(ge=0.5, le=5)
    end_scale: float = Field(ge=0.5, le=5)

    @model_validator(mode="after")
    def zoom_differs(self) -> "ZoomSpec":
        if self.start_scale == self.end_scale:
            raise ValueError("zoom start and end must differ")
        return self


class CameraMoveSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^cam_")
    shot_type: Literal[
        "dolly_in",
        "dolly_out",
        "truck_left",
        "truck_right",
        "orbit_cw",
        "orbit_ccw",
        "pan_left",
        "pan_right",
        "tilt_up",
        "tilt_down",
        "zoom_in",
        "zoom_out",
        "static",
    ]
    motion_type: Literal["camera_move", "lens_zoom", "orientation_only", "static"]
    technique: Literal["handheld", "gimbal", "tripod", "slider", "unknown"]
    subject_anchor: SubjectAnchor
    position_path: PositionPath | None = None
    orientation_path: OrientationPath | None = None
    zoom: ZoomSpec | None = None
    duration_s: int = Field(ge=2, le=10)
    easing: Literal["linear", "ease_in", "ease_out", "ease_in_out"]
    aspect_ratio: Literal["9:16", "16:9", "1:1", "4:3"]
    notes: list[str] = Field(default_factory=list, max_length=5)
    limitations: list[str] = Field(min_length=1, max_length=5)

    @model_validator(mode="after")
    def validate_consistency(self) -> "CameraMoveSpec":
        if self.motion_type == "camera_move":
            allowed = {"dolly_in", "dolly_out", "truck_left", "truck_right", "orbit_cw", "orbit_ccw"}
            if self.shot_type not in allowed or self.position_path is None:
                raise ValueError("camera_move requires position_path and a compatible shot_type")
            if self.zoom is not None:
                raise ValueError("camera_move forbids zoom")
            if self.shot_type in {"orbit_cw", "orbit_ccw"} and self.position_path.arc != self.shot_type.removeprefix("orbit_"):
                raise ValueError("orbit shot_type requires matching arc")
            if self.shot_type in {"dolly_in", "dolly_out", "truck_left", "truck_right"} and self.position_path.arc != "none":
                raise ValueError("dolly/truck requires arc=none")
        elif self.motion_type == "lens_zoom":
            if self.shot_type not in {"zoom_in", "zoom_out"} or self.zoom is None:
                raise ValueError("lens_zoom requires zoom and zoom_in/zoom_out")
            if self.position_path is not None or self.orientation_path is not None:
                raise ValueError("lens_zoom forbids position/orientation paths")
        elif self.motion_type == "orientation_only":
            if self.shot_type not in {"pan_left", "pan_right", "tilt_up", "tilt_down"}:
                raise ValueError("orientation_only shot_type is invalid")
            if self.orientation_path is None:
                raise ValueError("orientation_only requires orientation_path")
            if self.position_path is not None or self.zoom is not None:
                raise ValueError("orientation_only forbids position path and zoom")
        else:
            if self.shot_type != "static":
                raise ValueError("static requires shot_type=static")
            if self.position_path is not None or self.orientation_path is not None or self.zoom is not None:
                raise ValueError("static forbids movement fields")
        return self


def validate_visual_aid(value: dict | None) -> dict | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError("visual_aid must be an object or null")
    kind = value.get("type")
    if kind == "camera_move":
        camera = value.get("camera_move")
        if not isinstance(camera, dict):
            raise ValueError("camera_move visual_aid requires camera_move object")
        return {
            "type": "camera_move",
            "camera_move": CameraMoveSpec.model_validate(camera).model_dump(mode="json"),
        }
    if kind in {"timeline", "ratio_table"}:
        return value
    raise ValueError("unsupported visual_aid type")