package com.tutorialcoach.app.ui.screens.step

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope

import com.tutorialcoach.app.data.ProgressCache
import com.tutorialcoach.app.data.ProgressUpdate
import com.tutorialcoach.app.data.SessionActions
import com.tutorialcoach.app.data.toDto
import com.tutorialcoach.app.domain.DomainAnswer
import com.tutorialcoach.app.domain.DomainPlan
import com.tutorialcoach.app.domain.DomainStep
import com.tutorialcoach.app.domain.DomainTimer
import com.tutorialcoach.app.domain.ErrorMapper
import com.tutorialcoach.app.domain.TimerEngine
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

sealed interface AskUiState {
    data object Idle : AskUiState
    data object Sending : AskUiState
    data class Answer(val value: DomainAnswer) : AskUiState
}

data class StepUiState(
    val index: Int = 0,
    val timer: DomainTimer? = null,
    val timerRemainingS: Int = 0,
    val timerNeedsConfirmation: Boolean = false,
    val saving: Boolean = false,
    val error: String? = null,
    val retryable: Boolean = false,
    val message: String? = null,
    val askText: String = "",
    val ask: AskUiState = AskUiState.Idle,
)

class StepViewModel(
    private val gateway: SessionActions,
    private val localStore: ProgressCache,
    private val timerEngine: TimerEngine = TimerEngine(),
    private val wallClock: () -> Long = { System.currentTimeMillis() },
) : ViewModel() {
    private val _state = MutableStateFlow(StepUiState())
    val state: StateFlow<StepUiState> = _state.asStateFlow()

    val session = gateway.session
    val plan = gateway.plan
    val progress = gateway.progress

    private var initializedIndex = false
    private var ticker: Job? = null
    private var timerEpoch = 0

    init {
        restorePlan()
        restoreTimer()
        if (_state.value.timer?.state == "running") {
            ensureTicker()
        }
        viewModelScope.launch {
            gateway.plan.collect { current ->
                if (current != null && !initializedIndex) {
                    initializedIndex = true
                    val target = gateway.progress.value.currentStepId ?: localStore.currentStepId()
                    _state.update {
                        it.copy(index = indexOf(current, target))
                    }
                }
            }
        }
    }

    private fun restorePlan() {
        val current = gateway.session.value
        if (current?.currentPlanVersion != null && gateway.plan.value == null) {
            viewModelScope.launch {
                runCatching { gateway.loadPlan(current.id) }
            }
        }
    }

    private fun restoreTimer() {
        val timer = gateway.progress.value.timer ?: localStore.loadTimer()
        if (timer == null) return
        val needsConfirmation =
            timer.state == "running" && !timerEngine.isAnchorValid(timer, nowEpochMs())
        if (needsConfirmation) {
            val paused = timer.copy(
                state = "paused",
                anchorElapsedMs = null,
                updatedAt = timer.updatedAt,
            )
            _state.update {
                it.copy(
                    timer = paused,
                    timerRemainingS = paused.remainingS,
                    timerNeedsConfirmation = true,
                )
            }
        } else {
            _state.update {
                it.copy(
                    timer = timer,
                    timerRemainingS = timerEngine.remainingSeconds(timer),
                )
            }
        }
    }

    private fun beginTimerChange(): Int {
        timerEpoch += 1
        ticker?.cancel()
        ticker = null
        return timerEpoch
    }

    private fun ensureTicker() {
        val epoch = timerEpoch
        ticker?.cancel()
        ticker = viewModelScope.launch {
            while (true) {
                if (epoch != timerEpoch) return@launch
                val timer = _state.value.timer
                if (timer?.state != "running") return@launch
                delay(1_000)
                if (epoch != timerEpoch) return@launch
                val current = _state.value.timer
                if (current?.state != "running") return@launch
                val ticked = timerEngine.tick(current, nowEpochMs())
                if (epoch != timerEpoch) return@launch
                _state.update {
                    it.copy(
                        timer = ticked,
                        timerRemainingS = timerEngine.remainingSeconds(ticked),
                    )
                }
                if (ticked.state == "finished") {
                    if (epoch == timerEpoch) {
                        runCatching {
                            patchTimer(ticked)
                        }
                    }
                    return@launch
                }
            }
        }
    }

    fun next() {
        val currentPlan = gateway.plan.value ?: return
        val nextIndex = (_state.value.index + 1).coerceAtMost(currentPlan.steps.lastIndex)
        if (nextIndex != _state.value.index) {
            moveTo(nextIndex)
        }
    }

    fun previous() {
        val previousIndex = (_state.value.index - 1).coerceAtLeast(0)
        if (previousIndex != _state.value.index) {
            moveTo(previousIndex)
        }
    }

    private fun moveTo(index: Int) {
        val currentPlan = gateway.plan.value ?: return
        val step = currentPlan.steps.getOrNull(index) ?: return
        val epoch = beginTimerChange()
        runAction {
            val existing = gateway.progress.value.stepStatuses[step.id]
            val statuses = if (existing == null || existing == "not_started") {
                mapOf(step.id to "in_progress")
            } else {
                null
            }
            patch(
                currentStepId = step.id,
                includeCurrent = true,
                statuses = statuses,
                timer = null,
                includeTimer = true,
            )
            if (epoch == timerEpoch) {
                _state.update {
                    it.copy(index = index, timer = null, timerRemainingS = 0)
                }
            }
        }
    }

    fun startTimer() {
        val step = currentStep() ?: return
        val epoch = beginTimerChange()
        val timer = timerEngine.start(
            stepId = step.id,
            durationS = step.durationS.takeIf { it > 0 } ?: DEFAULT_TIMER_SECONDS,
            nowEpochMs = nowEpochMs(),
        )
        runAction {
            val existing = gateway.progress.value.stepStatuses[step.id]
            val statuses = if (existing == null || existing == "not_started") {
                mapOf(step.id to "in_progress")
            } else {
                null
            }
            patch(currentStepId = step.id, includeCurrent = true, statuses = statuses, timer = timer, includeTimer = true)
            if (epoch == timerEpoch) {
                _state.update {
                    it.copy(
                        timer = timer,
                        timerRemainingS = timer.remainingS,
                        timerNeedsConfirmation = false,
                        message = "计时开始。",
                    )
                }
                ensureTicker()
            }
        }
    }

    fun pauseTimer() {
        val timer = _state.value.timer ?: return
        val epoch = beginTimerChange()
        val paused = timerEngine.pause(timer, nowEpochMs())
        runAction {
            patch(currentStepId = timer.stepId, includeCurrent = true, timer = paused, includeTimer = true)
            if (epoch == timerEpoch) {
                _state.update {
                    it.copy(
                        timer = paused,
                        timerRemainingS = paused.remainingS,
                        message = "计时已暂停。",
                    )
                }
            }
        }
    }

    fun resumeTimer() {
        val timer = _state.value.timer ?: return
        val epoch = beginTimerChange()
        val resumed = timerEngine.resume(timer, nowEpochMs())
        runAction {
            patch(currentStepId = timer.stepId, includeCurrent = true, timer = resumed, includeTimer = true)
            if (epoch == timerEpoch) {
                _state.update {
                    it.copy(
                        timer = resumed,
                        timerRemainingS = timerEngine.remainingSeconds(resumed),
                        timerNeedsConfirmation = false,
                        message = "计时继续。",
                    )
                }
                ensureTicker()
            }
        }
    }

    fun resetTimer() {
        val step = currentStep() ?: return
        val epoch = beginTimerChange()
        val timer = timerEngine.start(
            stepId = step.id,
            durationS = step.durationS.takeIf { it > 0 } ?: DEFAULT_TIMER_SECONDS,
            nowEpochMs = nowEpochMs(),
        )
        runAction {
            patch(currentStepId = step.id, includeCurrent = true, timer = timer, includeTimer = true)
            if (epoch == timerEpoch) {
                _state.update {
                    it.copy(
                        timer = timer,
                        timerRemainingS = timer.remainingS,
                        timerNeedsConfirmation = false,
                        message = "计时已重置。",
                    )
                }
                ensureTicker()
            }
        }
    }

    fun confirmTimerContinue() {
        val timer = _state.value.timer ?: return
        val epoch = beginTimerChange()
        val resumed = timerEngine.resume(timer, nowEpochMs())
        runAction {
            patch(currentStepId = timer.stepId, includeCurrent = true, timer = resumed, includeTimer = true)
            if (epoch == timerEpoch) {
                _state.update {
                    it.copy(
                        timer = resumed,
                        timerRemainingS = timerEngine.remainingSeconds(resumed),
                        timerNeedsConfirmation = false,
                    )
                }
                ensureTicker()
            }
        }
    }

    fun confirmTimerReset() {
        resetTimer()
    }

    fun saveProgress() {
        val step = currentStep() ?: return
        val timer = _state.value.timer
        runAction {
            patch(
                currentStepId = step.id,
                includeCurrent = true,
                statuses = null,
                timer = timer,
                includeTimer = true,
            )
            localStore.saveProgress(gateway.progress.value)
            _state.update { it.copy(message = "进度已保存。") }
        }
    }

    fun completeStep() {
        val currentPlan = gateway.plan.value ?: return
        val step = currentStep() ?: return
        val status = gateway.progress.value.stepStatuses[step.id]
        if (status == "done" || status == "skipped") return
        val timer = _state.value.timer
        val paused = if (timer?.state == "running") timerEngine.pause(timer, nowEpochMs()) else timer
        val epoch = beginTimerChange()
        val nextIndex = _state.value.index + 1
        val nextStep = currentPlan.steps.getOrNull(nextIndex)
        val statuses = mutableMapOf(step.id to "done")
        if (nextStep != null) {
            val nextStatus = gateway.progress.value.stepStatuses[nextStep.id]
            if (nextStatus == null || nextStatus == "not_started") {
                statuses[nextStep.id] = "in_progress"
            }
        }
        val timerAfter = if (nextStep != null) null else paused
        runAction {
            patch(
                currentStepId = nextStep?.id ?: step.id,
                includeCurrent = true,
                statuses = statuses,
                evidenceLevels = mapOf(step.id to "self_reported"),
                timer = timerAfter,
                includeTimer = true,
            )
            if (epoch == timerEpoch) {
                _state.update {
                    it.copy(
                        index = if (nextStep != null) nextIndex else it.index,
                        timer = timerAfter,
                        timerRemainingS = timerAfter?.remainingS ?: 0,
                        message = "已标记完成（self_reported）。",
                    )
                }
            }
        }
    }

    fun skipStep() {
        val currentPlan = gateway.plan.value ?: return
        val step = currentStep() ?: return
        val epoch = beginTimerChange()
        val nextIndex = _state.value.index + 1
        val nextStep = currentPlan.steps.getOrNull(nextIndex)
        val statuses = mutableMapOf(step.id to "skipped")
        if (nextStep != null) {
            val nextStatus = gateway.progress.value.stepStatuses[nextStep.id]
            if (nextStatus == null || nextStatus == "not_started") {
                statuses[nextStep.id] = "in_progress"
            }
        }
        runAction {
            patch(
                currentStepId = nextStep?.id ?: step.id,
                includeCurrent = true,
                statuses = statuses,
                timer = null,
                includeTimer = true,
            )
            if (epoch == timerEpoch) {
                _state.update {
                    it.copy(
                        index = if (nextStep != null) nextIndex else it.index,
                        timer = null,
                        timerRemainingS = 0,
                        message = "已跳过本步。",
                    )
                }
            }
        }
    }

    fun pauseSession() {
        val current = gateway.session.value ?: return
        val epoch = beginTimerChange()
        runAction {
            val timer = _state.value.timer
            val paused = if (timer?.state == "running") timerEngine.pause(timer, nowEpochMs()) else timer
            if (paused != null) {
                patch(currentStepId = paused.stepId, includeCurrent = true, timer = paused, includeTimer = true)
            }
            gateway.pauseSession(current.id)
            if (epoch == timerEpoch) {
                _state.update {
                    it.copy(timer = paused, message = "练习已暂停；暂停期间不能写入进度。")
                }
            }
        }
    }

    fun resumeSession() {
        val current = gateway.session.value ?: return
        runAction {
            gateway.resumeSession(current.id)
            _state.update { it.copy(message = "练习已恢复。") }
        }
    }

    fun completeSession() {
        val current = gateway.session.value ?: return
        runAction {
            gateway.completeSession(current.id, rating = null, notes = "")
            _state.update { it.copy(message = "练习已标记完成（用户自报）。") }
        }
    }

    fun updateAskText(value: String) {
        _state.update { it.copy(askText = value) }
    }

    fun ask() {
        val question = _state.value.askText.trim()
        if (question.isEmpty()) {
            _state.update { it.copy(error = "请输入问题。", retryable = false) }
            return
        }
        val step = currentStep() ?: return
        val current = gateway.session.value ?: return
        val version = current.currentPlanVersion ?: return
        viewModelScope.launch {
            _state.update {
                it.copy(ask = AskUiState.Sending, error = null, message = null)
            }
            try {
                val answer = gateway.ask(current.id, question, step.id, version)
                _state.update { it.copy(ask = AskUiState.Answer(answer)) }
            } catch (error: Exception) {
                if (error is CancellationException) throw error
                _state.update {
                    it.copy(
                        ask = AskUiState.Idle,
                        error = ErrorMapper.message(error),
                        retryable = ErrorMapper.isRetryable(error),
                    )
                }
            }
        }
    }

    fun clearMessage() {
        _state.update { it.copy(message = null) }
    }

    fun dismissError() {
        _state.update { it.copy(error = null) }
    }

    private fun currentStep(): DomainStep? {
        val currentPlan = gateway.plan.value ?: return null
        return currentPlan.steps.getOrNull(_state.value.index)
    }

    private fun indexOf(plan: DomainPlan, stepId: String?): Int {
        if (stepId == null) return 0
        val index = plan.steps.indexOfFirst { it.id == stepId }
        return index.coerceAtLeast(0)
    }

    private suspend fun patchTimer(timer: DomainTimer) {
        patch(
            currentStepId = timer.stepId,
            includeCurrent = true,
            statuses = null,
            timer = timer,
            includeTimer = true,
        )
    }

    private suspend fun patch(
        currentStepId: String?,
        includeCurrent: Boolean,
        statuses: Map<String, String>? = null,
        evidenceLevels: Map<String, String>? = null,
        timer: DomainTimer? = null,
        includeTimer: Boolean = false,
    ) {
        val current = gateway.session.value ?: return
        val version = current.currentPlanVersion ?: return
        gateway.updateProgress(
            current.id,
            ProgressUpdate(
                basePlanVersion = version,
                currentStepId = currentStepId,
                includeCurrentStep = includeCurrent,
                stepStatuses = statuses,
                evidenceLevels = evidenceLevels,
                timer = timer?.toDto(),
                includeTimer = includeTimer,
            ),
        )
    }

    private fun runAction(block: suspend () -> Unit) {
        viewModelScope.launch {
            _state.update { it.copy(saving = true, error = null) }
            try {
                block()
            } catch (error: Exception) {
                if (error is CancellationException) throw error
                _state.update {
                    it.copy(
                        error = ErrorMapper.message(error),
                        retryable = ErrorMapper.isRetryable(error),
                    )
                }
            } finally {
                _state.update { it.copy(saving = false) }
            }
        }
    }

    private fun nowEpochMs(): Long = wallClock()

    override fun onCleared() {
        ticker?.cancel()
        super.onCleared()
    }

    private companion object {
        const val DEFAULT_TIMER_SECONDS = 300
    }
}