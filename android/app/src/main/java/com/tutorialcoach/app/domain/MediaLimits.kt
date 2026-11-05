package com.tutorialcoach.app.domain

object MediaLimits {
    const val MAX_IMAGE_BYTES = 10L * 1024 * 1024
    const val MAX_IMAGES = 4
    const val MAX_VIDEO_BYTES = 100L * 1024 * 1024
    const val MAX_VIDEO_DURATION_MS = 30_000L

    fun validateImage(sizeBytes: Long): String? = when {
        sizeBytes <= 0 -> "图片文件为空，请重新选择。"
        sizeBytes > MAX_IMAGE_BYTES -> "单张图片不能超过 10 MiB，请先压缩。"
        else -> null
    }

    fun validateVideo(durationMs: Long?, sizeBytes: Long?): String? = when {
        durationMs == null || durationMs <= 0 -> "无法读取视频时长，请换一段短片。"
        durationMs > MAX_VIDEO_DURATION_MS -> "视频不能超过 30 秒，请先裁剪。"
        sizeBytes == null || sizeBytes <= 0 -> "无法读取视频大小，请换一段短片。"
        sizeBytes > MAX_VIDEO_BYTES -> "视频不能超过 100 MiB，请先压缩。"
        else -> null
    }
}