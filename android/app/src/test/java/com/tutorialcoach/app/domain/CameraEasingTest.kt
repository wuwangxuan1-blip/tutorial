package com.tutorialcoach.app.domain

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Test

class CameraEasingTest {
    @Test
    fun linearAndEaseInOutDifferAtSameMidpoint() {
        val linear = CameraEasing.easedProgress("linear", 0.25f)
        val eased = CameraEasing.easedProgress("ease_in_out", 0.25f)
        assertEquals(0.25f, linear, 0.0001f)
        assertEquals(0.125f, eased, 0.0001f)
        assertNotEquals(linear, eased)

        assertEquals(0.875f, CameraEasing.easedProgress("ease_in_out", 0.75f), 0.0001f)
        assertEquals(0.5f, CameraEasing.easedProgress("ease_in_out", 0.5f), 0.0001f)
    }

    @Test
    fun easingIsClampedToTimelineBounds() {
        assertEquals(0f, CameraEasing.easedProgress("ease_in_out", -1f), 0.0001f)
        assertEquals(1f, CameraEasing.easedProgress("ease_in_out", 2f), 0.0001f)
    }
}