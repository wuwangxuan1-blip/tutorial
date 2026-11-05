package com.tutorialcoach.app.data

import android.os.SystemClock
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

private const val REFRESH_INTERVAL_MS = 1_000L

class RateLimitGate(
    private val scope: CoroutineScope = CoroutineScope(SupervisorJob() + Dispatchers.Default),
    private val clock: () -> Long = { SystemClock.elapsedRealtime() },
) {
    private val _remainingSeconds = MutableStateFlow(0)
    val remainingSeconds: StateFlow<Int> = _remainingSeconds.asStateFlow()

    @Volatile
    private var deadlineMs: Long = 0L

    @Volatile
    private var ticker: Job? = null

    fun isBlocked(): Boolean = clock() < deadlineMs

    fun start(retryAfterS: Int) {
        val seconds = retryAfterS.coerceAtLeast(1)
        deadlineMs = clock() + seconds * 1_000L
        ticker?.cancel()
        _remainingSeconds.value = seconds
        ticker = scope.launch {
            while (true) {
                val remainingMs = (deadlineMs - clock()).coerceAtLeast(0L)
                _remainingSeconds.value =
                    ((remainingMs + REFRESH_INTERVAL_MS - 1) / REFRESH_INTERVAL_MS).toInt()
                if (remainingMs == 0L) break
                delay(REFRESH_INTERVAL_MS)
            }
        }
    }
}