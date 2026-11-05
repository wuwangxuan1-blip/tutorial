package com.tutorialcoach.app.domain

data class CameraPlaybackState(
    val progress: Float = 0f,
    val playing: Boolean = false,
) {
    fun play(): CameraPlaybackState =
        if (progress >= 1f) copy(progress = 0f, playing = true) else copy(playing = true)

    fun pause(): CameraPlaybackState = copy(playing = false)

    fun replay(): CameraPlaybackState = CameraPlaybackState(progress = 0f, playing = true)

    fun seek(progress: Float): CameraPlaybackState =
        copy(progress = progress.coerceIn(0f, 1f), playing = false)

    fun tick(deltaSeconds: Float, durationS: Int): CameraPlaybackState {
        if (!playing || durationS <= 0 || deltaSeconds <= 0f) return this
        val next = (progress + deltaSeconds / durationS).coerceIn(0f, 1f)
        return copy(progress = next, playing = next < 1f)
    }
}