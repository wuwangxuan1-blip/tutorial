package com.tutorialcoach.app.domain

import org.junit.Assert.assertTrue
import org.junit.Test

class CameraMoveValidatorTest {
    private fun orbit(
        shotType: String = "orbit_cw",
        motionType: String = "camera_move",
        start: DomainPoint = DomainPoint(0.3, 0.7),
        end: DomainPoint = DomainPoint(0.7, 0.3),
        arc: String = "cw",
        durationS: Int = 8,
        limitations: List<String> = listOf("2D 俯视示意，不代表真实焦距。"),
    ) = DomainCameraMoveSpec(
        id = "cam_1",
        shotType = shotType,
        motionType = motionType,
        technique = "handheld",
        subjectAnchor = DomainSubjectAnchor(0.5, 0.5, "咖啡杯"),
        positionPath = DomainPositionPath(
            space = "normalized_top_down",
            start = start,
            end = end,
            control = null,
            arc = arc,
        ),
        orientationPath = null,
        zoom = null,
        durationS = durationS,
        easing = "ease_in_out",
        aspectRatio = "9:16",
        notes = emptyList(),
        limitations = limitations,
    )

    @Test
    fun validOrbitIsAccepted() {
        assertTrue(CameraMoveValidator.validate(orbit()).isEmpty())
    }

    @Test
    fun invalidCombinationsAndValuesAreRejected() {
        assertTrue(CameraMoveValidator.validate(orbit(durationS = 1)).isNotEmpty())
        assertTrue(CameraMoveValidator.validate(orbit(shotType = "pan_left")).isNotEmpty())
        assertTrue(CameraMoveValidator.validate(orbit(start = DomainPoint(0.3, 0.7), end = DomainPoint(0.3, 0.7))).isNotEmpty())
        assertTrue(CameraMoveValidator.validate(orbit(arc = "none")).isNotEmpty())
        assertTrue(CameraMoveValidator.validate(orbit(start = DomainPoint(Double.NaN, 0.7))).isNotEmpty())
        assertTrue(
            CameraMoveValidator.validate(orbit(start = DomainPoint(1.2, 0.7))).isNotEmpty(),
        )
        assertTrue(
            CameraMoveValidator.validate(orbit(limitations = listOf("没有说明示意限制。"))).isNotEmpty(),
        )
    }

    @Test
    fun zoomAndOrientationDirectionsAreChecked() {
        val zoom = DomainCameraMoveSpec(
            id = "cam_zoom",
            shotType = "zoom_in",
            motionType = "lens_zoom",
            technique = "tripod",
            subjectAnchor = DomainSubjectAnchor(0.5, 0.5, "杯口"),
            positionPath = null,
            orientationPath = null,
            zoom = DomainZoomSpec(1.0, 2.0),
            durationS = 4,
            easing = "ease_in",
            aspectRatio = "16:9",
            notes = emptyList(),
            limitations = listOf("2D 取景框示意，不代表真实焦距。"),
        )
        assertTrue(CameraMoveValidator.validate(zoom).isEmpty())
        assertTrue(CameraMoveValidator.validate(zoom.copy(zoom = DomainZoomSpec(2.0, 1.0))).isNotEmpty())

        val orientation = DomainCameraMoveSpec(
            id = "cam_pan",
            shotType = "pan_left",
            motionType = "orientation_only",
            technique = "tripod",
            subjectAnchor = DomainSubjectAnchor(0.5, 0.5, "杯口"),
            positionPath = null,
            orientationPath = DomainOrientationPath(-30.0, 30.0, 0.0, 0.0),
            zoom = null,
            durationS = 4,
            easing = "linear",
            aspectRatio = "16:9",
            notes = emptyList(),
            limitations = listOf("2D 朝向示意，不代表真实镜头。"),
        )
        assertTrue(CameraMoveValidator.validate(orientation).isNotEmpty())
    }
}