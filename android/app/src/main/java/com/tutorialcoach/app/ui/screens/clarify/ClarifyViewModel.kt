package com.tutorialcoach.app.ui.screens.clarify

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.tutorialcoach.app.data.AnswerDto
import com.tutorialcoach.app.data.SessionRepository
import com.tutorialcoach.app.domain.DomainSession
import com.tutorialcoach.app.domain.ErrorMapper
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.receiveAsFlow
import kotlinx.coroutines.launch
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonPrimitive

sealed interface ClarifyUiState {
    data object Idle : ClarifyUiState
    data object Loading : ClarifyUiState
    data class Error(val message: String, val retryable: Boolean) : ClarifyUiState
}

sealed interface ClarifyEvent {
    data object Ready : ClarifyEvent
}

class ClarifyViewModel(
    private val repository: SessionRepository,
) : ViewModel() {
    val session: StateFlow<DomainSession?> = repository.session

    private val _uiState = MutableStateFlow<ClarifyUiState>(ClarifyUiState.Idle)
    val uiState: StateFlow<ClarifyUiState> = _uiState.asStateFlow()

    private val _events = Channel<ClarifyEvent>(Channel.BUFFERED)
    val events = _events.receiveAsFlow()

    fun submit(values: Map<String, String>) {
        val current = repository.session.value ?: return
        if (current.status != "clarifying") {
            _events.trySend(ClarifyEvent.Ready)
            return
        }
        val answers = mutableListOf<AnswerDto>()
        for (question in current.questions) {
            val raw = values[question.id]?.trim().orEmpty()
            if (raw.isEmpty()) {
                if (question.required) {
                    _uiState.value = ClarifyUiState.Error("请回答必填问题：${question.prompt}", retryable = false)
                    return
                }
                continue
            }
            val element = when (question.kind) {
                "number" -> {
                    val number = raw.toIntOrNull()
                    if (number == null) {
                        _uiState.value = ClarifyUiState.Error("请为“${question.prompt}”填写整数。", retryable = false)
                        return
                    }
                    JsonPrimitive(number)
                }
                "boolean" -> {
                    if (raw != "true" && raw != "false") {
                        _uiState.value = ClarifyUiState.Error("请为“${question.prompt}”选择是或否。", retryable = false)
                        return
                    }
                    JsonPrimitive(raw == "true")
                }
                "multi_choice" -> JsonArray(raw.split(",").map { JsonPrimitive(it.trim()) })
                else -> JsonPrimitive(raw)
            }
            answers += AnswerDto(question.id, element)
        }
        if (answers.isEmpty()) {
            _uiState.value = ClarifyUiState.Error("请至少回答一个问题。", retryable = false)
            return
        }
        viewModelScope.launch {
            _uiState.value = ClarifyUiState.Loading
            try {
                val updated = repository.submitAnswers(current.id, answers)
                _uiState.value = ClarifyUiState.Idle
                if (updated.status == "ready") {
                    _events.send(ClarifyEvent.Ready)
                }
            } catch (error: Exception) {
                if (error is CancellationException) throw error
                _uiState.value = ClarifyUiState.Error(ErrorMapper.message(error), ErrorMapper.isRetryable(error))
            }
        }
    }

    fun dismissError() {
        _uiState.value = ClarifyUiState.Idle
    }
}