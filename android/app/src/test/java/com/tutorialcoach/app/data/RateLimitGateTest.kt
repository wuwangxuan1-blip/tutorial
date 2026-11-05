package com.tutorialcoach.app.data

import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class RateLimitGateTest {
    @Test
    fun deadlineExpiresEvenWhenRefreshCoroutineHasNotRun() = runTest {
        var nowMs = 0L
        val gate = RateLimitGate(backgroundScope, { nowMs })
        gate.start(7)
        assertEquals(7, gate.remainingSeconds.value)

        nowMs = 7_001L
        assertFalse(gate.isBlocked())

        runCurrent()
        assertEquals(0, gate.remainingSeconds.value)
        assertFalse(gate.isBlocked())
    }

    @Test
    fun remainingSecondsRoundsUpAndBlocksBeforeDeadline() = runTest {
        var nowMs = 1_000L
        val gate = RateLimitGate(backgroundScope, { nowMs })
        gate.start(7)
        assertEquals(7, gate.remainingSeconds.value)

        nowMs = 3_001L
        runCurrent()
        assertTrue(gate.isBlocked())
        assertEquals(5, gate.remainingSeconds.value)
    }
}