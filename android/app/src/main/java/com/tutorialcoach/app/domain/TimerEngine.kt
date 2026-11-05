package com.tutorialcoach.app.domain

import android.os.SystemClock
import java.time.Instant
import kotlin.math.ceil

class TimerEngine(
    private val clock: () -> Long = { SystemClock.elapsedRealtime() },
) {
    fun start(stepId: String, durationS: Int, nowEpochMs: Long): DomainTimer {
        val duration = durationS.coerceAtLeast(1)
        return DomainTimer(
            stepId = stepId,
            state = "running",
            durationS = duration,
            remainingS = duration,
            anchorElapsedMs = clock(),
            savedAtEpochMs = nowEpochMs,
            updatedAt = iso(nowEpochMs),
        )
    }

    fun pause(timer: DomainTimer, nowEpochMs: Long): DomainTimer {
        val ticked = tick(timer, nowEpochMs)
        return ticked.copy(
            state = "paused",
            remainingS = remainingSeconds(ticked),
            anchorElapsedMs = null,
            savedAtEpochMs = nowEpochMs,
            updatedAt = iso(nowEpochMs),
        )
    }

    fun resume(timer: DomainTimer, nowEpochMs: Long): DomainTimer = timer.copy(
        state = "running",
        anchorElapsedMs = clock(),
        savedAtEpochMs = nowEpochMs,
        updatedAt = iso(nowEpochMs),
    )

    fun tick(timer: DomainTimer, nowEpochMs: Long): DomainTimer {
        if (timer.state != "running") return timer
        val anchor = timer.anchorElapsedMs ?: return timer.copy(
            state = "paused",
            anchorElapsedMs = null,
            savedAtEpochMs = nowEpochMs,
            updatedAt = iso(nowEpochMs),
        )
        val elapsedMs = (clock() - anchor).coerceAtLeast(0L)
        val consumedSeconds = (elapsedMs / 1_000L).toInt()
        if (consumedSeconds <= 0) return timer
        val remaining = (timer.remainingS - consumedSeconds).coerceAtLeast(0)
        if (remaining == 0) {
            return timer.copy(
                state = "finished",
                remainingS = 0,
                anchorElapsedMs = null,
                savedAtEpochMs = nowEpochMs,
                updatedAt = iso(nowEpochMs),
            )
        }
        return timer.copy(
            remainingS = remaining,
            anchorElapsedMs = anchor + consumedSeconds * 1_000L,
            savedAtEpochMs = nowEpochMs,
            updatedAt = iso(nowEpochMs),
        )
    }

    fun remainingSeconds(timer: DomainTimer): Int {
        if (timer.state == "finished") return 0
        if (timer.state != "running") return timer.remainingS.coerceAtLeast(0)
        val anchor = timer.anchorElapsedMs ?: return timer.remainingS.coerceAtLeast(0)
        val elapsedMs = (clock() - anchor).coerceAtLeast(0L)
        val remainingMs = timer.remainingS * 1_000L - elapsedMs
        return ceil(remainingMs / 1_000.0).toInt().coerceAtLeast(0)
    }

    fun isAnchorValid(timer: DomainTimer, nowEpochMs: Long): Boolean {
        val anchor = timer.anchorElapsedMs ?: return true
        if (clock() < anchor) return false
        val wallDiff = nowEpochMs - timer.savedAtEpochMs
        if (wallDiff < 0) return false
        return wallDiff <= MAX_ANCHOR_AGE_MS
    }

    private fun iso(epochMs: Long): String = Instant.ofEpochMilli(epochMs).toString()

    companion object {
        private const val MAX_ANCHOR_AGE_MS = 7L * 24 * 3600 * 1000
    }
}