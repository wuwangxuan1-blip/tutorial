package com.tutorialcoach.app.domain

import com.tutorialcoach.app.data.ApiException
import com.tutorialcoach.app.data.NetworkException

object ErrorMapper {
    fun message(error: Throwable): String = when (error) {
        is NetworkException -> "无法连接本地服务，请检查服务端与 adb reverse tcp:8000 tcp:8000。"
        is ApiException -> when (error.code) {
            "MODEL_NOT_CONFIGURED" -> "服务端未配置模型 Key，请在 server/.env 配置后重启服务端。"
            "MODEL_AUTH_FAILED" -> "模型 Key 无效，请在服务端检查配置。"
            "MODEL_INSUFFICIENT_BALANCE" -> "模型账户余额不足，请在服务端处理。"
            "MODEL_RATE_LIMITED" -> {
                val seconds = error.retryAfterS
                if (seconds != null) "模型繁忙，请 $seconds 秒后重试。" else "模型繁忙，请稍后重试。"
            }
            "MODEL_TIMEOUT" -> "模型请求超时，请重试。"
            "MODEL_BAD_OUTPUT" -> "模型返回格式异常，已重试一次仍失败，请重试或缩短输入。"
            "PLAN_LOCKED" -> "已有步骤进度，不能全量重新生成。"
            "VERSION_CONFLICT" -> "计划版本已变化，请刷新后重试。"
            "DOMAIN_MISMATCH" -> "当前阶段仅支持烹饪领域的计划生成。"
            "JOB_EXPIRED" -> "任务结果已过期，请重新生成。"
            "INVALID_REQUEST" -> error.message.ifBlank { "请求参数不符合要求。" }
            "NOT_FOUND" -> "资源不存在，请返回重试。"
            else -> error.message.ifBlank { "发生错误（${error.code}），请稍后重试。" }
        }
        else -> "发生未知错误，请稍后重试。"
    }

    fun isRetryable(error: Throwable): Boolean = when (error) {
        is NetworkException -> true
        is ApiException -> error.retryable
        else -> false
    }
}