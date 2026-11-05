package com.tutorialcoach.app.domain

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class CameraPlaybackStateTest {
    @Test
    fun playPauseReplayAndTick() {
        var state = CameraPlaybackState()
        state = state.play()
        assertTrue(state.playing)

        state = state.tick(1f, 8)
        assertEquals(0.125f, state.progress, 0.001f)

        state = state.pause()
        assertFalse(state.playing)
        assertEquals(0.125f, state.progress, 0.001f)

        state = state.replay()
        assertTrue(state.playing)
        assertEquals(0f, state.progress, 0.001f)

        state = state.tick(8f, 8)
        assertEquals(1f, state.progress, 0.001f)
        assertFalse(state.playing)

        state = state.play()
        assertEquals(0f, state.progress, 0.001f)
        assertTrue(state.playing)

        state = state.seek(0.4f)
        assertEquals(0.4f, state.progress, 0.001f)
        assertFalse(state.playing)
        state = state.seek(1.4f)
        assertEquals(1f, state.progress, 0.001f)
    }
}