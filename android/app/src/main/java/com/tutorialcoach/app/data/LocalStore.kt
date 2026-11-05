package com.tutorialcoach.app.data

import android.content.Context
import com.tutorialcoach.app.domain.DomainProgress
import com.tutorialcoach.app.domain.DomainSession
import com.tutorialcoach.app.domain.DomainTimer
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json

class LocalStore(context: Context) : ProgressCache {
    private val prefs = context.applicationContext.getSharedPreferences(
        "tutorial_coach_local",
        Context.MODE_PRIVATE,
    )
    private val json = Json {
        ignoreUnknownKeys = true
        explicitNulls = false
        encodeDefaults = true
    }

    val lastSessionId: String?
        get() = prefs.getString(KEY_SESSION, null)

    override fun currentStepId(): String? = prefs.getString(KEY_STEP, null)

    fun saveSession(session: DomainSession) {
        prefs.edit().putString(KEY_SESSION, session.id).apply()
    }

    override fun saveProgress(progress: DomainProgress) {
        val editor = prefs.edit()
        val stepId = progress.currentStepId
        if (stepId == null) {
            editor.remove(KEY_STEP)
        } else {
            editor.putString(KEY_STEP, stepId)
        }
        val timer = progress.timer
        if (timer == null) {
            editor.remove(KEY_TIMER)
        } else {
            editor.putString(KEY_TIMER, json.encodeToString(TimerDto.serializer(), timer.toDto()))
        }
        editor.apply()
    }

    override fun loadTimer(): DomainTimer? {
        val raw = prefs.getString(KEY_TIMER, null) ?: return null
        return runCatching {
            json.decodeFromString(TimerDto.serializer(), raw).toDomain()
        }.getOrNull()
    }

    fun clear() {
        prefs.edit().clear().apply()
    }

    private companion object {
        const val KEY_SESSION = "last_session_id"
        const val KEY_STEP = "current_step_id"
        const val KEY_TIMER = "timer"
    }
}