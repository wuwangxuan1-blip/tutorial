package com.tutorialcoach.app.ui.screens.media

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.tutorialcoach.app.data.FeedbackGateway
import com.tutorialcoach.app.data.FeedbackJobRequestDto
import com.tutorialcoach.app.data.JobDto
import com.tutorialcoach.app.data.MediaDto
import com.tutorialcoach.app.data.SessionActions
import com.tutorialcoach.app.domain.DomainFeedback
import com.tutorialcoach.app.domain.ErrorMapper
import com.tutorialcoach.app.domain.MediaLimits
import com.tutorialcoach.app.platform.MediaLoader
import com.tutorialcoach.app.platform.MediaValidationException
import com.tutorialcoach.app.platform.PreparedImage
import com.tutorialcoach.app.platform.PreparedVideo
import java.io.File
import java.util.UUID
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

data class MediaUiState(
    val images: List<PreparedImage> = emptyList(),
    val video: PreparedVideo? = null,
    val note: String = "",
    val privacyAccepted: Boolean = false,
    val uploading: Boolean = false,
    val uploadProgress: Float = 0f,
    val submitting: Boolean = false,
    val uploaded: Map<String, MediaDto> = emptyMap(),
    val feedback: DomainFeedback? = null,
    val evidenceFrames: Map<String, File> = emptyMap(),
    val error: String? = null,
    val retryable: Boolean = false,
    val message: String? = null,
)

fun evidenceFrameKey(mediaId: String, frameIndex: Int?, timestampS: Double?): String? {
    if (frameIndex == null || timestampS == null) return null
    return "$mediaId|$frameIndex|$timestampS"
}

fun MediaUiState.evidenceFrameFile(
    mediaId: String,
    frameIndex: Int?,
    timestampS: Double?,
): File? = evidenceFrameKey(mediaId, frameIndex, timestampS)?.let { evidenceFrames[it] }

private data class UploadItem(
    val key: String,
    val file: File,
    val mime: String,
    val kind: String,
)

class MediaViewModel(
    private val sessionActions: SessionActions,
    private val feedbackGateway: FeedbackGateway,
    private val loader: MediaLoader,
    private val ioDispatcher: CoroutineDispatcher = Dispatchers.IO,
) : ViewModel() {
    private val _state = MutableStateFlow(MediaUiState())
    val state: StateFlow<MediaUiState> = _state.asStateFlow()

    val session = sessionActions.session
    val plan = sessionActions.plan
    val progress = sessionActions.progress

    fun addImages(uris: List<String>) {
        if (uris.isEmpty()) return
        try {
            val room = MediaLimits.MAX_IMAGES - _state.value.images.size
            if (room <= 0) {
                _state.update { it.copy(error = "最多选择 4 张图片。", retryable = false) }
                return
            }
            val prepared = uris.take(room).map { loader.prepareImage(it) }
            prepared.forEach { image ->
                MediaLimits.validateImage(image.file.length())?.let {
                    throw MediaValidationException(it)
                }
            }
            deleteEvidenceFrames()
            _state.update {
                it.copy(
                    images = (it.images + prepared).take(MediaLimits.MAX_IMAGES),
                    video = null,
                    uploaded = emptyMap(),
                    feedback = null,
                    evidenceFrames = emptyMap(),
                    error = null,
                    message = null,
                )
            }
        } catch (error: Exception) {
            _state.update {
                it.copy(error = mediaError(error), retryable = false)
            }
        }
    }

    fun setVideo(uri: String) {
        try {
            val prepared = loader.prepareVideo(uri)
            deleteEvidenceFrames()
            _state.update {
                it.copy(
                    video = prepared,
                    images = emptyList(),
                    uploaded = emptyMap(),
                    feedback = null,
                    evidenceFrames = emptyMap(),
                    error = null,
                    message = null,
                )
            }
        } catch (error: Exception) {
            _state.update {
                it.copy(error = mediaError(error), retryable = false)
            }
        }
    }

    fun removeImage(image: PreparedImage) {
        image.file.delete()
        deleteEvidenceFrames()
        _state.update {
            it.copy(
                images = it.images - image,
                uploaded = emptyMap(),
                feedback = null,
                evidenceFrames = emptyMap(),
            )
        }
    }

    fun clearMedia() {
        _state.value.images.forEach { it.file.delete() }
        _state.value.video?.file?.delete()
        _state.value.video?.thumbnail?.delete()
        deleteEvidenceFrames()
        _state.update {
            it.copy(
                images = emptyList(),
                video = null,
                uploaded = emptyMap(),
                feedback = null,
                evidenceFrames = emptyMap(),
                error = null,
            )
        }
    }

    fun updateNote(value: String) {
        _state.update { it.copy(note = value.take(500)) }
    }

    fun setPrivacyAccepted(value: Boolean) {
        _state.update { it.copy(privacyAccepted = value) }
    }

    fun dismissError() {
        _state.update { it.copy(error = null) }
    }

    fun submit() {
        if (!_state.value.privacyAccepted) {
            _state.update { it.copy(error = "请先阅读并同意隐私提示。", retryable = false) }
            return
        }
        if (_state.value.images.isEmpty() && _state.value.video == null) {
            _state.update { it.copy(error = "请先选择 1–4 张图片或 1 段短片。", retryable = false) }
            return
        }
        runSubmit()
    }

    fun retry() {
        if (_state.value.uploaded.size < mediaItems().size) {
            runSubmit()
        } else {
            runFeedbackOnly()
        }
    }

    private fun runSubmit() {
        viewModelScope.launch {
            _state.update { it.copy(submitting = true, uploading = true, error = null, message = null) }
            try {
                val items = mediaItems()
                for (item in items) {
                    if (_state.value.uploaded.containsKey(item.key)) continue
                    val uploaded = feedbackGateway.uploadMedia(
                        item.file,
                        item.mime,
                        item.kind,
                    ) { progressValue ->
                        val completed = _state.value.uploaded.size.toFloat() / items.size
                        _state.update {
                            it.copy(
                                uploadProgress = (completed + progressValue / items.size).coerceIn(0f, 1f),
                            )
                        }
                    }
                    _state.update {
                        it.copy(uploaded = it.uploaded + (item.key to uploaded))
                    }
                }
                _state.update { it.copy(uploading = false, uploadProgress = 1f) }
                submitFeedback(items)
            } catch (error: Exception) {
                if (error is CancellationException) throw error
                _state.update {
                    it.copy(
                        submitting = false,
                        uploading = false,
                        error = mediaError(error),
                        retryable = true,
                    )
                }
            }
        }
    }

    private fun runFeedbackOnly() {
        viewModelScope.launch {
            _state.update { it.copy(submitting = true, error = null, message = null) }
            try {
                submitFeedback(mediaItems())
            } catch (error: Exception) {
                if (error is CancellationException) throw error
                _state.update {
                    it.copy(submitting = false, error = mediaError(error), retryable = true)
                }
            }
        }
    }

    private suspend fun submitFeedback(items: List<UploadItem>) {
        val currentSession = sessionActions.session.value ?: error("会话不存在")
        val currentPlan = sessionActions.plan.value ?: error("还没有计划")
        val version = currentSession.currentPlanVersion ?: error("还没有计划版本")
        val stepId = sessionActions.progress.value.currentStepId
            ?: currentPlan.steps.firstOrNull()?.id
            ?: error("没有可反馈的步骤")
        val mediaIds = items.mapNotNull { _state.value.uploaded[it.key]?.id }
        if (mediaIds.size != items.size) error("媒体尚未全部上传")
        val job = feedbackGateway.createFeedbackJob(
            currentSession.id,
            FeedbackJobRequestDto(
                stepId = stepId,
                planVersion = version,
                mediaIds = mediaIds,
                note = _state.value.note.trim(),
            ),
            UUID.randomUUID().toString(),
        )
        val finished = waitForJob(job)
        if (finished.status != "succeeded") {
            val code = finished.error?.error?.code
            val message = if (code == "VISION_UNSUPPORTED") {
                "模型视觉不可用：当前服务端视觉模型未配置或端点不支持图片；未生成反馈。"
            } else {
                finished.error?.error?.message ?: "媒体反馈失败，请重试；未生成假反馈。"
            }
            _state.update {
                it.copy(
                    submitting = false,
                    error = message,
                    retryable = finished.error?.error?.retryable ?: true,
                )
            }
            return
        }
        val feedbackId = finished.result?.feedbackId ?: error("反馈结果缺少 feedback_id")
        val feedback = feedbackGateway.getFeedback(feedbackId)
        val evidenceFrames = loadEvidenceFrames(feedback)
        _state.update {
            it.copy(
                submitting = false,
                feedback = feedback,
                evidenceFrames = evidenceFrames,
                message = "反馈已生成；媒体证据与局限见下方。",
            )
        }
    }

    private suspend fun loadEvidenceFrames(feedback: DomainFeedback): Map<String, File> {
        val video = _state.value.video ?: return emptyMap()
        val videoMediaId = _state.value.uploaded["video"]?.id ?: return emptyMap()
        return withContext(ioDispatcher) {
            feedback.observations.mapNotNull { observation ->
                val evidence = observation.evidence
                if (evidence.kind != "video_frame" || evidence.mediaId != videoMediaId) {
                    return@mapNotNull null
                }
                val timestamp = evidence.timestampS ?: return@mapNotNull null
                val key = evidenceFrameKey(evidence.mediaId, evidence.frameIndex, timestamp)
                    ?: return@mapNotNull null
                val frame = loader.extractEvidenceFrame(video.file, timestamp)
                    ?: return@mapNotNull null
                key to frame
            }.toMap()
        }
    }

    private fun deleteEvidenceFrames() {
        _state.value.evidenceFrames.values.forEach { it.delete() }
    }

    private suspend fun waitForJob(job: JobDto): JobDto {
        var current = job
        val deadline = System.currentTimeMillis() + 240_000L
        while (current.status == "queued" || current.status == "running") {
            if (System.currentTimeMillis() > deadline) {
                return current.copy(error = null)
            }
            delay(500)
            current = feedbackGateway.getJob(current.id)
        }
        return current
    }

    private fun mediaItems(): List<UploadItem> {
        val items = _state.value.images.mapIndexed { index, image ->
            UploadItem("image_$index", image.file, "image/jpeg", "image")
        }.toMutableList()
        _state.value.video?.let {
            items.add(UploadItem("video", it.file, it.mime, "video"))
        }
        return items
    }

    private fun mediaError(error: Throwable): String = when (error) {
        is MediaValidationException -> error.message ?: "媒体不符合要求。"
        else -> ErrorMapper.message(error)
    }

    override fun onCleared() {
        _state.value.images.forEach { it.file.delete() }
        _state.value.video?.file?.delete()
        _state.value.video?.thumbnail?.delete()
        deleteEvidenceFrames()
        super.onCleared()
    }
}