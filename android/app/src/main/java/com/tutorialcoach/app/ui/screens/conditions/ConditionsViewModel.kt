package com.tutorialcoach.app.ui.screens.conditions

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.tutorialcoach.app.data.SessionActions
import com.tutorialcoach.app.domain.DomainImpact
import com.tutorialcoach.app.domain.ErrorMapper
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonPrimitive

data class ConditionsUiState(
    val timeBudget: String = "",
    val people: String = "",
    val servings: String = "",
    val notes: String = "",
    val saving: Boolean = false,
    val error: String? = null,
    val impact: DomainImpact? = null,
    val message: String? = null,
)

class ConditionsViewModel(
    private val gateway: SessionActions,
) : ViewModel() {
    private val _state = MutableStateFlow(ConditionsUiState())
    val state: StateFlow<ConditionsUiState> = _state.asStateFlow()

    val session = gateway.session

    init {
        val conditions = gateway.session.value?.conditions.orEmpty()
        _state.value = ConditionsUiState(
            timeBudget = conditions["time_budget_min"].orEmpty(),
            people = conditions["people"].orEmpty(),
            servings = conditions["servings"].orEmpty(),
            notes = conditions["notes"].orEmpty(),
        )
    }

    fun updateTimeBudget(value: String) {
        _state.update { it.copy(timeBudget = value, impact = null, error = null) }
    }

    fun updatePeople(value: String) {
        _state.update { it.copy(people = value, impact = null, error = null) }
    }

    fun updateServings(value: String) {
        _state.update { it.copy(servings = value, impact = null, error = null) }
    }

    fun updateNotes(value: String) {
        _state.update { it.copy(notes = value, impact = null, error = null) }
    }

    fun submit() {
        val current = gateway.session.value ?: return
        val updates = mutableMapOf<String, JsonElement?>()
        parseNumber(_state.value.timeBudget, "时间预算", updates, "time_budget_min") ?: return
        parseNumber(_state.value.people, "人数", updates, "people") ?: return
        parseNumber(_state.value.servings, "份量", updates, "servings") ?: return
        val notes = _state.value.notes.trim()
        if (notes.isNotEmpty()) {
            updates["notes"] = JsonPrimitive(notes)
        }
        if (updates.isEmpty()) {
            _state.update { it.copy(error = "至少修改一个字段。", impact = null) }
            return
        }
        runPatch(current.id, current.currentPlanVersion, updates)
    }

    fun clearNotes() {
        val current = gateway.session.value ?: return
        runPatch(current.id, current.currentPlanVersion, mapOf("notes" to null))
    }

    private fun parseNumber(
        raw: String,
        label: String,
        updates: MutableMap<String, JsonElement?>,
        field: String,
    ): Unit? {
        val text = raw.trim()
        if (text.isEmpty()) return Unit
        val value = text.toIntOrNull()
        if (value == null) {
            _state.update { it.copy(error = "$label 必须是整数。", impact = null) }
            return null
        }
        updates[field] = JsonPrimitive(value)
        return Unit
    }

    private fun runPatch(
        sessionId: String,
        basePlanVersion: Int?,
        updates: Map<String, JsonElement?>,
    ) {
        viewModelScope.launch {
            _state.update { it.copy(saving = true, error = null, message = null) }
            try {
                val impact = gateway.patchConditions(sessionId, basePlanVersion, updates)
                _state.update {
                    it.copy(
                        saving = false,
                        impact = impact,
                        message = impact.message,
                        notes = if (updates.containsKey("notes")) "" else it.notes,
                    )
                }
            } catch (error: Exception) {
                if (error is CancellationException) throw error
                _state.update {
                    it.copy(
                        saving = false,
                        error = ErrorMapper.message(error),
                    )
                }
            }
        }
    }
}