package com.tutorialcoach.app.ui.screens.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.tutorialcoach.app.data.CapabilitiesDto
import com.tutorialcoach.app.data.HealthDto
import com.tutorialcoach.app.data.SessionRepository
import com.tutorialcoach.app.domain.ErrorMapper
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

sealed interface DiagnosticsUiState {
    data object Loading : DiagnosticsUiState
    data class Ready(val health: HealthDto, val capabilities: CapabilitiesDto) : DiagnosticsUiState
    data class Error(val message: String) : DiagnosticsUiState
}

class DiagnosticsViewModel(
    private val repository: SessionRepository,
) : ViewModel() {
    private val _uiState = MutableStateFlow<DiagnosticsUiState>(DiagnosticsUiState.Loading)
    val uiState: StateFlow<DiagnosticsUiState> = _uiState.asStateFlow()

    init {
        refresh()
    }

    fun refresh() {
        viewModelScope.launch {
            _uiState.value = DiagnosticsUiState.Loading
            try {
                val health = repository.health()
                val capabilities = repository.capabilities()
                _uiState.value = DiagnosticsUiState.Ready(health, capabilities)
            } catch (error: Exception) {
                if (error is CancellationException) throw error
                _uiState.value = DiagnosticsUiState.Error(ErrorMapper.message(error))
            }
        }
    }
}