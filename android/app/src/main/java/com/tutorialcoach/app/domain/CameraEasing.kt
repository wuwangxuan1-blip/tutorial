package com.tutorialcoach.app.domain

object CameraEasing {
    fun easedProgress(easing: String, progress: Float): Float {
        val t = progress.coerceIn(0f, 1f)
        return when (easing) {
            "linear" -> t
            "ease_in" -> t * t
            "ease_out" -> 1f - (1f - t) * (1f - t)
            "ease_in_out" ->
                if (t < 0.5f) 2f * t * t
                else 1f - ((-2f * t + 2f) * (-2f * t + 2f)) / 2f
            else -> t
        }
    }
}