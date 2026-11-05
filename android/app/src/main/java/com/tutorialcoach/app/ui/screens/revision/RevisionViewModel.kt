package com.tutorialcoach.app.ui.screens.revision

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.tutorialcoach.app.data.JobDto
import com.tutorialcoach.app.data.SessionActions
import com.tutorialcoach.app.domain.DomainRevision
import com.tutorialcoach.app.domain.ErrorMapper
import java.util.UUID
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class RevisionUiState(
    val revisions: List<DomainRevision> = emptyList(),
    val reason: String = "",
    val loading: Boolean = false,
    val submitting: Boolean = false,
    val error: String? = null,
    val message: String? = null,
)

class RevisionViewModel(
    private val gateway: SessionActions,
) : ViewModel() {
    private val _state = MutableStateFlow(RevisionUiState())
    val state: StateFlow<RevisionUiState> = _state.asStateFlow()

    val session = gateway.session
    val plan = gateway.plan

    init {
        load()
    }

    fun updateReason(value: String) {
        _state.update { it.copy(reason = value, error = null) }
    }

    fun load() {
        val current = gateway.session.value ?: return
        viewModelScope.launch {
            _state.update { it.copy(loading = true, error = null) }
            try {
                val revisions = gateway.listRevisions(current.id)
                _state.update { it.copy(loading = false, revisions = revisions) }
            } catch (error: Exception) {
                if (error is CancellationException) throw error
                _state.update {
                    it.copy(loading = false, error = ErrorMapper.message(error))
                }
            }
        }
    }

    fun createRevision() {
        val reason = _state.value.reason.trim()
        if (reason.isEmpty()) {
            _state.update { it.copy(error = "请输入修订原因。") }
            return
        }
        val current = gateway.session.value ?: return
        val version = current.currentPlanVersion ?: return
        viewModelScope.launch {
            _state.update { it.copy(submitting = true, error = null, message = null) }
            try {
                val job = gateway.createRevisionJob(
                    current.id,
                    version,
                    reason,
                    UUID.randomUUID().toString(),
                )
                val finished = waitForJob(job)
                if (finished.status != "succeeded") {
                    _state.update {
                        it.copy(
                            submitting = false,
                            error = finished.error?.error?.message ?: "修订生成失败，请重试。",
                        )
                    }
                    return@launch
                }
                val revisions = gateway.listRevisions(current.id)
                val revisionId = finished.result?.revisionId
                _state.update {
                    it.copy(
                        submitting = false,
                        revisions = revisions,
                        reason = "",
                        message = if (revisionId == null) {
                            "模型判断无需调整。"
                        } else {
                            "修订已生成，请审阅后应用或拒绝。"
                        },
                    )
                }
            } catch (error: Exception) {
                if (error is CancellationException) throw error
                _state.update {
                    it.copy(submitting = false, error = ErrorMapper.message(error))
                }
            }
        }
    }

    fun apply(revision: DomainRevision) {
        val current = gateway.session.value ?: return
        val version = current.currentPlanVersion ?: return
        viewModelScope.launch {
            _state.update { it.copy(submitting = true, error = null, message = null) }
            try {
                gateway.applyRevision(current.id, revision.id, version)
                val revisions = gateway.listRevisions(current.id)
                _state.update {
                    it.copy(
                        submitting = false,
                        revisions = revisions,
                        message = "修订已应用；计划版本 +1，已完成/跳过步骤保持不变。",
                    )
                }
            } catch (error: Exception) {
                if (error is CancellationException) throw error
                _state.update {
                    it.copy(submitting = false, error = ErrorMapper.message(error))
                }
            }
        }
    }

    fun reject(revision: DomainRevision) {
        val current = gateway.session.value ?: return
        viewModelScope.launch {
            _state.update { it.copy(submitting = true, error = null, message = null) }
            try {
                gateway.rejectRevision(current.id, revision.id, "用户拒绝")
                val revisions = gateway.listRevisions(current.id)
                _state.update {
                    it.copy(
                        submitting = false,
                        revisions = revisions,
                        message = "修订已拒绝。",
                    )
                }
            } catch (error: Exception) {
                if (error is CancellationException) throw error
                _state.update {
                    it.copy(submitting = false, error = ErrorMapper.message(error))
                }
            }
        }
    }

    private val pollTimeoutMs = 180_000L

    private suspend fun waitForJob(job: JobDto): JobDto {
        var current = job
        val deadline = System.currentTimeMillis() + pollTimeoutMs
        while (current.status == "queued" || current.status == "running") {
            if (System.currentTimeMillis() > deadline) {
                return current
            }
            delay(500)
            current = gateway.getJob(current.id)
        }
        return current
    }
}