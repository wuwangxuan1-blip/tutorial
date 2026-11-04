package com.tutorialcoach.app.ui.screens.home

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.tutorialcoach.app.data.SessionRepository
import com.tutorialcoach.app.domain.ErrorMapper
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.receiveAsFlow
import kotlinx.coroutines.launch

sealed interface HomeUiState {
    data object Idle : HomeUiState
    data object Loading : HomeUiState
    data class Error(val message: String, val retryable: Boolean) : HomeUiState
}

sealed interface HomeEvent {
    data class Created(val status: String) : HomeEvent
}

class HomeViewModel(
    private val repository: SessionRepository,
) : ViewModel() {
    private val _uiState = MutableStateFlow<HomeUiState>(HomeUiState.Idle)
    val uiState: StateFlow<HomeUiState> = _uiState.asStateFlow()

    private val _serviceStatus = MutableStateFlow<String?>(null)
    val serviceStatus: StateFlow<String?> = _serviceStatus.asStateFlow()

    private val _events = Channel<HomeEvent>(Channel.BUFFERED)
    val events = _events.receiveAsFlow()

    init {
        refreshHealth()
    }

    fun refreshHealth() {
        viewModelScope.launch {
            _serviceStatus.value = try {
                repository.health().status
            } catch (error: Exception) {
                if (error is CancellationException) throw error
                "offline"
            }
        }
    }

    fun create(goal: String, domain: String) {
        if (goal.isBlank()) {
            _uiState.value = HomeUiState.Error("请输入实践目标。", retryable = false)
            return
        }
        if (goal.length > 500) {
            _uiState.value = HomeUiState.Error("目标最多 500 字。", retryable = false)
            return
        }
        if (domain !in setOf("cooking", "photography", "software", "coffee")) {
            _uiState.value = HomeUiState.Error("请选择领域。", retryable = false)
            return
        }
        viewModelScope.launch {
            _uiState.value = HomeUiState.Loading
            try {
                val session = repository.createSession(goal.trim(), domain)
                _events.send(HomeEvent.Created(session.status))
                _uiState.value = HomeUiState.Idle
            } catch (error: Exception) {
                if (error is CancellationException) throw error
                _uiState.value = HomeUiState.Error(ErrorMapper.message(error), ErrorMapper.isRetryable(error))
            }
        }
    }

    fun dismissError() {
        _uiState.value = HomeUiState.Idle
    }
}