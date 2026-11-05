package com.tutorialcoach.app.domain

import com.tutorialcoach.app.data.ApiException
import com.tutorialcoach.app.data.NetworkException
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ErrorMapperTest {
    @Test
    fun networkErrorShowsAdbReverseHint() {
        val message = ErrorMapper.message(NetworkException("boom"))
        assertTrue(message.contains("adb reverse"))
        assertTrue(ErrorMapper.isRetryable(NetworkException("boom")))
    }

    @Test
    fun modelNotConfiguredIsNotRetryable() {
        val error = ApiException("MODEL_NOT_CONFIGURED", "服务端未配置模型 Key。", retryable = false)
        assertTrue(ErrorMapper.message(error).contains("server/.env"))
        assertFalse(ErrorMapper.isRetryable(error))
    }

    @Test
    fun rateLimitedUsesRetryAfter() {
        val error = ApiException(
            code = "MODEL_RATE_LIMITED",
            message = "模型限流。",
            retryable = true,
            retryAfterS = 5,
        )
        assertEquals("模型繁忙，请 5 秒后重试。", ErrorMapper.message(error))
        assertTrue(ErrorMapper.isRetryable(error))
    }

    @Test
    fun planLockedHasClearMessage() {
        val error = ApiException("PLAN_LOCKED", "已有进度。", retryable = false)
        assertTrue(ErrorMapper.message(error).contains("不能全量重新生成"))
        assertFalse(ErrorMapper.isRetryable(error))
    }

    @Test
    fun modelRefusedIsNotRetryable() {
        val error = ApiException("MODEL_REFUSED", "模型拒绝处理该请求。", retryable = false)
        assertTrue(ErrorMapper.message(error).contains("模型拒绝处理"))
        assertFalse(ErrorMapper.isRetryable(error))
    }
}