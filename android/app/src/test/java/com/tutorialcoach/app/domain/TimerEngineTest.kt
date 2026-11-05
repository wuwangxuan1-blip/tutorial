package com.tutorialcoach.app.domain

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class TimerEngineTest {
    @Test
    fun startAndTickUseRemainingSnapshot() {
        var elapsed = 0L
        val engine = TimerEngine { elapsed }
        val timer = engine.start("step_1", 300, 1_000_000L)
        assertEquals("running", timer.state)
        assertEquals(300, timer.remainingS)
        assertEquals(0L, timer.anchorElapsedMs)

        elapsed = 1_500L
        val afterOneSecond = engine.tick(timer, 1_001_500L)
        assertEquals(299, afterOneSecond.remainingS)

        elapsed = 300_000L
        val finished = engine.tick(afterOneSecond, 1_300_000L)
        assertEquals("finished", finished.state)
        assertEquals(0, finished.remainingS)
        assertNull(finished.anchorElapsedMs)
        assertEquals(0, engine.remainingSeconds(finished))
    }

    @Test
    fun pauseAndResumeKeepRemainingTime() {
        var elapsed = 0L
        val engine = TimerEngine { elapsed }
        val timer = engine.start("step_2", 300, 1_000_000L)

        elapsed = 60_000L
        val ticked = engine.tick(timer, 1_060_000L)
        assertEquals(240, ticked.remainingS)

        val paused = engine.pause(ticked, 1_060_000L)
        assertEquals("paused", paused.state)
        assertEquals(240, paused.remainingS)
        assertNull(paused.anchorElapsedMs)

        elapsed = 120_000L
        val resumed = engine.resume(paused, 1_120_000L)
        assertEquals("running", resumed.state)
        assertEquals(240, resumed.remainingS)
        assertEquals(120_000L, resumed.anchorElapsedMs)

        elapsed = 180_000L
        assertEquals(180, engine.tick(resumed, 1_180_000L).remainingS)
    }

    @Test
    fun restoreDetectsRebootOrClockAnomaly() {
        var elapsed = 5_000L
        val engine = TimerEngine { elapsed }
        val timer = engine.start("step_1", 300, 1_000_000L)

        assertTrue(engine.isAnchorValid(timer, 1_000_500L))

        elapsed = 1_000L
        assertFalse(engine.isAnchorValid(timer, 1_001_000L))

        elapsed = 5_000L
        assertFalse(engine.isAnchorValid(timer, 999_000L))
    }
}