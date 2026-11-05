package com.tutorialcoach.app.domain

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class MediaLimitsTest {
    @Test
    fun imageSizeLimitIsTenMiB() {
        assertNull(MediaLimits.validateImage(10L * 1024 * 1024))
        assertEquals(
            "单张图片不能超过 10 MiB，请先压缩。",
            MediaLimits.validateImage(10L * 1024 * 1024 + 1),
        )
        assertEquals("图片文件为空，请重新选择。", MediaLimits.validateImage(0))
    }

    @Test
    fun videoDurationAndSizeLimits() {
        assertNull(MediaLimits.validateVideo(30_000, 100L * 1024 * 1024))
        assertEquals(
            "视频不能超过 30 秒，请先裁剪。",
            MediaLimits.validateVideo(30_001, 1024),
        )
        assertEquals(
            "视频不能超过 100 MiB，请先压缩。",
            MediaLimits.validateVideo(10_000, 100L * 1024 * 1024 + 1),
        )
        assertEquals("无法读取视频时长，请换一段短片。", MediaLimits.validateVideo(null, 1024))
    }
}