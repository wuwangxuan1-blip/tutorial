package com.tutorialcoach.app.ui.screens.plan

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.tutorialcoach.app.data.ApiException
import com.tutorialcoach.app.data.NetworkException
import com.tutorialcoach.app.data.PlanGateway
import com.tutorialcoach.app.domain.DomainPlan
import com.tutorialcoach.app.domain.DomainSession
import com.tutorialcoach.app.domain.ErrorMapper
import com.tutorialcoach.app.domain.PlanValidator
import java.util.UUID
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

sealed interface PlanUiState {
    data object Idle : PlanUiState
    data class Working(val progress: Int, val stage: String) : PlanUiState
    data class Ready(val plan: DomainPlan) : PlanUiState
    data class Error(val message: String, val retryable: Boolean) : PlanUiState
    data class RateLimited(val message: String, val remainingSeconds: Int) : PlanUiState
}

class PlanViewModel(
    private val repository: PlanGateway,
) : ViewModel() {
    val session: StateFlow<DomainSession?> = repository.session

    private val _uiState = MutableStateFlow<PlanUiState>(
        repository.plan.value?.let { PlanUiState.Ready(it) } ?: PlanUiState.Idle,
    )
    val uiState: StateFlow<PlanUiState> = _uiState.asStateFlow()

    private var observedSessionId: String? = repository.session.value?.id
    private var pollJob: Job? = null
    private var planIdempotencyKey: String? = null
    private var pendingPlanSessionId: String? = null
    private var rateLimitTicker: Job? = null
    private var rateLimitRemaining: Int = 0
    private var rateLimitMessage: String = ""

    init {
        viewModelScope.launch {
            repository.session.collect { current ->
                if (current?.id != observedSessionId) {
                    observedSessionId = current?.id
                    pollJob?.cancel()
                    rateLimitTicker?.cancel()
                    rateLimitTicker = null
                    rateLimitRemaining = 0
                    rateLimitMessage = ""
                    planIdempotencyKey = null
                    pendingPlanSessionId = null
                    _uiState.value = repository.plan.value?.let { PlanUiState.Ready(it) } ?: PlanUiState.Idle
                }
            }
        }
    }

    fun generate() {
        if (rateLimitRemaining > 0) return
        if (pollJob?.isActive == true) return
        if (pendingPlanSessionId != null) {
            retry()
            return
        }
        val current = repository.session.value
        if (current == null) {
            _uiState.value = PlanUiState.Error("会话未加载，请返回首页重新创建。", retryable = false)
            return
        }
        if (current.status != "ready") {
            _uiState.value = PlanUiState.Error("请先完成澄清问题。", retryable = false)
            return
        }
        pollJob?.cancel()
        val idempotencyKey = planIdempotencyKey ?: UUID.randomUUID().toString().also {
            planIdempotencyKey = it
        }
        pollJob = viewModelScope.launch {
            _uiState.value = PlanUiState.Working(0, "queued")
            try {
                var job = repository.createPlanJob(current.id, current.currentPlanVersion, idempotencyKey)
                val deadline = System.currentTimeMillis() + 180_000
                while (job.status == "queued" || job.status == "running") {
                    if (repository.session.value?.id != current.id) return@launch
                    if (System.currentTimeMillis() > deadline) {
                        throw ApiException("MODEL_TIMEOUT", "生成计划超时，请重试。", retryable = true)
                    }
                    _uiState.value = PlanUiState.Working(job.progress, job.stage)
                    delay(1000)
                    job = repository.getJob(job.id)
                }
                when (job.status) {
                    "succeeded" -> {
                        planIdempotencyKey = null
                        pendingPlanSessionId = current.id
                        _uiState.value = PlanUiState.Working(100, "loading_plan")
                        fetchPlan(current.id)
                    }
                    "failed" -> {
                        planIdempotencyKey = null
                        val error = job.error?.error
                        val message = error?.message?.takeIf(String::isNotBlank) ?: "生成计划失败，请重试。"
                        if (error?.code == "MODEL_RATE_LIMITED") {
                            startRateLimit(message, error.retryAfterS ?: 1)
                        } else {
                            _uiState.value = PlanUiState.Error(
                                message,
                                error?.retryable ?: true,
                            )
                        }
                    }
                    else -> {
                        planIdempotencyKey = null
                        _uiState.value = PlanUiState.Error("任务状态异常：${job.status}", retryable = true)
                    }
                }
            } catch (error: Exception) {
                if (error is CancellationException) throw error
                if (error !is NetworkException) {
                    planIdempotencyKey = null
                }
                _uiState.value = PlanUiState.Error(ErrorMapper.message(error), ErrorMapper.isRetryable(error))
            }
        }
    }

    fun retry() {
        if (rateLimitRemaining > 0) return
        val pending = pendingPlanSessionId
        if (pending == null) {
            generate()
            return
        }
        if (pollJob?.isActive == true) return
        pollJob?.cancel()
        pollJob = viewModelScope.launch {
            _uiState.value = PlanUiState.Working(100, "loading_plan")
            fetchPlan(pending)
        }
    }

    private fun startRateLimit(message: String, retryAfterS: Int) {
        val seconds = retryAfterS.coerceAtLeast(1)
        rateLimitTicker?.cancel()
        rateLimitRemaining = seconds
        rateLimitMessage = message
        _uiState.value = PlanUiState.RateLimited(message, seconds)
        rateLimitTicker = viewModelScope.launch {
            while (rateLimitRemaining > 0) {
                _uiState.value = PlanUiState.RateLimited(rateLimitMessage, rateLimitRemaining)
                delay(1000)
                rateLimitRemaining -= 1
            }
            _uiState.value = PlanUiState.Error(rateLimitMessage, retryable = true)
        }
    }

    private suspend fun fetchPlan(sessionId: String) {
        try {
            val plan = repository.loadPlan(sessionId)
            if (repository.session.value?.id != sessionId) return
            val errors = PlanValidator.validate(plan)
            if (errors.isEmpty()) {
                pendingPlanSessionId = null
                _uiState.value = PlanUiState.Ready(plan)
            } else {
                pendingPlanSessionId = null
                _uiState.value = PlanUiState.Error(
                    "模型计划结构异常：${errors.first()}",
                    retryable = true,
                )
            }
        } catch (error: Exception) {
            if (error is CancellationException) throw error
            _uiState.value = PlanUiState.Error(
                "计划已生成，但获取计划失败：${ErrorMapper.message(error)}",
                retryable = true,
            )
        }
    }

    fun dismissError() {
        if (pendingPlanSessionId != null) {
            retry()
            return
        }
        _uiState.value = repository.plan.value?.let { PlanUiState.Ready(it) } ?: PlanUiState.Idle
    }
}