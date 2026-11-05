package com.tutorialcoach.app.domain

object CameraMoveValidator {
    private val motionTypes = setOf("camera_move", "lens_zoom", "orientation_only", "static")
    private val shotTypes = setOf(
        "dolly_in", "dolly_out", "truck_left", "truck_right", "orbit_cw", "orbit_ccw",
        "pan_left", "pan_right", "tilt_up", "tilt_down", "zoom_in", "zoom_out", "static",
    )
    private val easings = setOf("linear", "ease_in", "ease_out", "ease_in_out")
    private val aspects = setOf("9:16", "16:9", "1:1", "4:3")

    fun validate(spec: DomainCameraMoveSpec): List<String> {
        val errors = mutableListOf<String>()
        if (!spec.id.startsWith("cam_")) errors += "运镜 id 必须以 cam_ 开头。"
        if (spec.motionType !in motionTypes) errors += "运动类型无效。"
        if (spec.shotType !in shotTypes) errors += "镜头类型无效。"
        if (spec.durationS !in 2..10) errors += "运镜时长必须在 2–10 秒。"
        if (spec.easing !in easings) errors += "缓动类型无效。"
        if (spec.aspectRatio !in aspects) errors += "画幅无效。"

        validatePoint(spec.subjectAnchor.x, spec.subjectAnchor.y, "主体锚点", errors)
        if (spec.subjectAnchor.label.isBlank() || spec.subjectAnchor.label.length > 40) {
            errors += "主体标签必须为 1–40 字。"
        }
        if (spec.notes.size > 5 || spec.notes.any { it.length !in 1..200 }) {
            errors += "备注最多 5 条，每条 1–200 字。"
        }
        if (spec.limitations.isEmpty() || spec.limitations.size > 5) {
            errors += "局限说明必须为 1–5 条。"
        } else if (spec.limitations.any { it.length !in 1..200 }) {
            errors += "局限说明每条 1–200 字。"
        } else if (spec.limitations.none { "2D" in it || "俯视" in it || "焦距" in it }) {
            errors += "局限说明必须写明 2D/俯视/焦距限制。"
        }

        when (spec.motionType) {
            "camera_move" -> validateCameraMove(spec, errors)
            "lens_zoom" -> validateLensZoom(spec, errors)
            "orientation_only" -> validateOrientation(spec, errors)
            "static" -> {
                if (spec.shotType != "static") errors += "静止运镜必须使用 shot_type=static。"
                if (spec.positionPath != null || spec.orientationPath != null || spec.zoom != null) {
                    errors += "静止运镜不得包含路径或变焦。"
                }
            }
        }
        return errors.distinct()
    }

    private fun validateCameraMove(spec: DomainCameraMoveSpec, errors: MutableList<String>) {
        val allowed = setOf("dolly_in", "dolly_out", "truck_left", "truck_right", "orbit_cw", "orbit_ccw")
        if (spec.shotType !in allowed) errors += "机位移动的镜头类型不匹配。"
        val path = spec.positionPath
        if (path == null) {
            errors += "机位移动必须提供 position_path。"
        } else {
            validatePoint(path.start.x, path.start.y, "路径起点", errors)
            validatePoint(path.end.x, path.end.y, "路径终点", errors)
            path.control?.let { validatePoint(it.x, it.y, "路径控制点", errors) }
            if (path.start.x == path.end.x && path.start.y == path.end.y) {
                errors += "路径起点与终点不能相同。"
            }
            if (path.space != "normalized_top_down") errors += "路径坐标必须为 normalized_top_down。"
            if (spec.shotType == "orbit_cw" && path.arc != "cw") errors += "orbit_cw 必须 arc=cw。"
            if (spec.shotType == "orbit_ccw" && path.arc != "ccw") errors += "orbit_ccw 必须 arc=ccw。"
            if (spec.shotType in setOf("dolly_in", "dolly_out", "truck_left", "truck_right") && path.arc != "none") {
                errors += "dolly/truck 必须 arc=none。"
            }
        }
        if (spec.zoom != null) errors += "机位移动不得同时使用变焦。"
    }

    private fun validateLensZoom(spec: DomainCameraMoveSpec, errors: MutableList<String>) {
        val zoom = spec.zoom
        if (spec.shotType !in setOf("zoom_in", "zoom_out") || zoom == null) {
            errors += "镜头变焦必须提供 zoom 并使用 zoom_in/zoom_out。"
        }
        if (spec.positionPath != null || spec.orientationPath != null) {
            errors += "镜头变焦不得同时使用机位或朝向路径。"
        }
        if (zoom != null) {
            validateScale(zoom.startScale, "起始缩放", errors)
            validateScale(zoom.endScale, "结束缩放", errors)
            if (zoom.startScale == zoom.endScale) errors += "变焦起止值不能相同。"
            if (spec.shotType == "zoom_in" && zoom.endScale <= zoom.startScale) {
                errors += "zoom_in 需要结束缩放大于起始缩放。"
            }
            if (spec.shotType == "zoom_out" && zoom.endScale >= zoom.startScale) {
                errors += "zoom_out 需要结束缩放小于起始缩放。"
            }
        }
    }

    private fun validateOrientation(spec: DomainCameraMoveSpec, errors: MutableList<String>) {
        val path = spec.orientationPath
        if (spec.shotType !in setOf("pan_left", "pan_right", "tilt_up", "tilt_down")) {
            errors += "原地转向的镜头类型不匹配。"
        }
        if (path == null) {
            errors += "原地转向必须提供 orientation_path。"
            return
        }
        if (spec.positionPath != null || spec.zoom != null) {
            errors += "原地转向不得同时使用机位路径或变焦。"
        }
        validateOrientationValues(path.startYawDeg, path.endYawDeg, path.startPitchDeg, path.endPitchDeg, errors)
        if (path.startYawDeg == path.endYawDeg && path.startPitchDeg == path.endPitchDeg) {
            errors += "朝向必须至少改变 yaw 或 pitch。"
        }
        val yawDelta = path.endYawDeg - path.startYawDeg
        val pitchDelta = path.endPitchDeg - path.startPitchDeg
        if (spec.shotType == "pan_left" && yawDelta >= 0) errors += "pan_left 需要 yaw 递减。"
        if (spec.shotType == "pan_right" && yawDelta <= 0) errors += "pan_right 需要 yaw 递增。"
        if (spec.shotType == "tilt_up" && pitchDelta <= 0) errors += "tilt_up 需要 pitch 递增。"
        if (spec.shotType == "tilt_down" && pitchDelta >= 0) errors += "tilt_down 需要 pitch 递减。"
    }

    private fun validateOrientationValues(
        startYaw: Double,
        endYaw: Double,
        startPitch: Double,
        endPitch: Double,
        errors: MutableList<String>,
    ) {
        if (!startYaw.isFinite() || startYaw !in -180.0..180.0 ||
            !endYaw.isFinite() || endYaw !in -180.0..180.0
        ) {
            errors += "yaw 必须在 -180–180 度且为有限数。"
        }
        if (!startPitch.isFinite() || startPitch !in -90.0..90.0 ||
            !endPitch.isFinite() || endPitch !in -90.0..90.0
        ) {
            errors += "pitch 必须在 -90–90 度且为有限数。"
        }
    }

    private fun validatePoint(x: Double, y: Double, label: String, errors: MutableList<String>) {
        if (!x.isFinite() || !y.isFinite() || x !in 0.0..1.0 || y !in 0.0..1.0) {
            errors += "$label 必须是 0–1 的有限归一化坐标。"
        }
    }

    private fun validateScale(value: Double, label: String, errors: MutableList<String>) {
        if (!value.isFinite() || value !in 0.5..5.0) {
            errors += "$label 必须在 0.5–5 且为有限数。"
        }
    }
}