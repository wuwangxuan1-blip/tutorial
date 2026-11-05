package com.tutorialcoach.app.data

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject

@Serializable
data class QuestionDto(
    @SerialName("id") val id: String,
    @SerialName("field") val field: String,
    @SerialName("prompt") val prompt: String,
    @SerialName("kind") val kind: String,
    @SerialName("required") val required: Boolean = false,
    @SerialName("options") val options: List<String> = emptyList(),
    @SerialName("unit") val unit: String? = null,
    @SerialName("help") val help: String = "",
)

@Serializable
data class TimerDto(
    @SerialName("step_id") val stepId: String,
    @SerialName("state") val state: String,
    @SerialName("duration_s") val durationS: Int,
    @SerialName("remaining_s") val remainingS: Int,
    @SerialName("anchor_elapsed_ms") val anchorElapsedMs: Long? = null,
    @SerialName("saved_at_epoch_ms") val savedAtEpochMs: Long,
    @SerialName("updated_at") val updatedAt: String,
)

@Serializable
data class ProgressDto(
    @SerialName("current_step_id") val currentStepId: String? = null,
    @SerialName("step_statuses") val stepStatuses: Map<String, String> = emptyMap(),
    @SerialName("evidence_levels") val evidenceLevels: Map<String, String> = emptyMap(),
    @SerialName("timer") val timer: TimerDto? = null,
    @SerialName("updated_at") val updatedAt: String = "",
)

@Serializable
data class SessionDto(
    @SerialName("id") val id: String,
    @SerialName("domain") val domain: String,
    @SerialName("goal") val goal: String,
    @SerialName("status") val status: String,
    @SerialName("conditions") val conditions: JsonObject = JsonObject(emptyMap()),
    @SerialName("questions") val questions: List<QuestionDto> = emptyList(),
    @SerialName("reference_ids") val referenceIds: List<String> = emptyList(),
    @SerialName("current_plan_version") val currentPlanVersion: Int? = null,
    @SerialName("progress") val progress: ProgressDto = ProgressDto(),
    @SerialName("outcome") val outcome: JsonObject? = null,
    @SerialName("created_at") val createdAt: String = "",
    @SerialName("updated_at") val updatedAt: String = "",
)

@Serializable
data class PreparationDto(
    @SerialName("id") val id: String,
    @SerialName("text") val text: String,
    @SerialName("optional") val optional: Boolean = false,
)

@Serializable
data class StepDto(
    @SerialName("id") val id: String,
    @SerialName("order") val order: Int,
    @SerialName("phase") val phase: String,
    @SerialName("title") val title: String,
    @SerialName("instruction") val instruction: String,
    @SerialName("why") val why: String = "",
    @SerialName("duration_s") val durationS: Int = 0,
    @SerialName("completion_criteria") val completionCriteria: List<String> = emptyList(),
    @SerialName("safety") val safety: List<String> = emptyList(),
    @SerialName("common_mistakes") val commonMistakes: List<String> = emptyList(),
    @SerialName("timer") val timer: JsonElement? = null,
    @SerialName("visual_aid") val visualAid: JsonElement? = null,
    @SerialName("evidence_hint") val evidenceHint: String = "",
    @SerialName("media_prompt") val mediaPrompt: String = "",
)

@Serializable
data class PlanDto(
    @SerialName("id") val id: String,
    @SerialName("session_id") val sessionId: String,
    @SerialName("version") val version: Int,
    @SerialName("domain") val domain: String,
    @SerialName("title") val title: String,
    @SerialName("summary") val summary: String = "",
    @SerialName("assumptions") val assumptions: List<String> = emptyList(),
    @SerialName("preparation") val preparation: List<PreparationDto> = emptyList(),
    @SerialName("steps") val steps: List<StepDto> = emptyList(),
    @SerialName("total_estimated_min") val totalEstimatedMin: Int = 0,
    @SerialName("safety_notes") val safetyNotes: List<String> = emptyList(),
    @SerialName("reference_ids") val referenceIds: List<String> = emptyList(),
    @SerialName("created_at") val createdAt: String = "",
)

@Serializable
data class ErrorDetailDto(
    @SerialName("code") val code: String = "",
    @SerialName("message") val message: String = "",
    @SerialName("retryable") val retryable: Boolean = false,
    @SerialName("retry_after_s") val retryAfterS: Int? = null,
    @SerialName("request_id") val requestId: String = "",
    @SerialName("details") val details: JsonObject = JsonObject(emptyMap()),
)

@Serializable
data class ErrorEnvelopeDto(
    @SerialName("error") val error: ErrorDetailDto,
)

@Serializable
data class JobResultDto(
    @SerialName("plan_id") val planId: String? = null,
    @SerialName("plan_version") val planVersion: Int? = null,
    @SerialName("revision_id") val revisionId: String? = null,
    @SerialName("feedback_id") val feedbackId: String? = null,
)

@Serializable
data class JobDto(
    @SerialName("id") val id: String,
    @SerialName("type") val type: String,
    @SerialName("status") val status: String,
    @SerialName("progress") val progress: Int = 0,
    @SerialName("stage") val stage: String = "",
    @SerialName("session_id") val sessionId: String,
    @SerialName("created_at") val createdAt: String = "",
    @SerialName("updated_at") val updatedAt: String = "",
    @SerialName("expires_at") val expiresAt: String = "",
    @SerialName("result") val result: JobResultDto? = null,
    @SerialName("error") val error: ErrorEnvelopeDto? = null,
)

@Serializable
data class HealthChecksDto(
    @SerialName("store") val store: Boolean = false,
    @SerialName("ffmpeg") val ffmpeg: Boolean = false,
    @SerialName("model_configured") val modelConfigured: Boolean = false,
)

@Serializable
data class HealthDto(
    @SerialName("status") val status: String = "",
    @SerialName("api_version") val apiVersion: String = "",
    @SerialName("time") val time: String = "",
    @SerialName("checks") val checks: HealthChecksDto = HealthChecksDto(),
)

@Serializable
data class ModelCapabilityDto(
    @SerialName("text_model") val textModel: String? = null,
    @SerialName("vision_model") val visionModel: String? = null,
    @SerialName("configured") val configured: Boolean = false,
    @SerialName("vision_supported") val visionSupported: Boolean? = null,
    @SerialName("probe_at") val probeAt: String? = null,
    @SerialName("audio_analysis") val audioAnalysis: Boolean = false,
)

@Serializable
data class CapabilitiesDto(
    @SerialName("api_version") val apiVersion: String = "",
    @SerialName("domains") val domains: List<String> = emptyList(),
    @SerialName("model") val model: ModelCapabilityDto = ModelCapabilityDto(),
)

@Serializable
data class CreateSessionRequest(
    @SerialName("domain") val domain: String,
    @SerialName("goal") val goal: String,
    @SerialName("reference_ids") val referenceIds: List<String> = emptyList(),
    @SerialName("conditions") val conditions: JsonObject = JsonObject(emptyMap()),
)

@Serializable
data class AnswerDto(
    @SerialName("question_id") val questionId: String,
    @SerialName("value") val value: JsonElement,
)

@Serializable
data class AnswerSubmissionDto(
    @SerialName("answers") val answers: List<AnswerDto>,
)

@Serializable
data class CreatePlanJobRequest(
    @SerialName("base_plan_version") val basePlanVersion: Int? = null,
)

@Serializable
data class CompleteRequestDto(
    @SerialName("rating") val rating: Int? = null,
    @SerialName("notes") val notes: String = "",
)

@Serializable
data class AskRequestDto(
    @SerialName("question") val question: String,
    @SerialName("step_id") val stepId: String,
    @SerialName("plan_version") val planVersion: Int,
)

@Serializable
data class RevisionJobRequestDto(
    @SerialName("feedback_id") val feedbackId: String? = null,
    @SerialName("base_plan_version") val basePlanVersion: Int,
    @SerialName("request_reason") val requestReason: String,
)

@Serializable
data class RevisionApplyRequestDto(
    @SerialName("base_plan_version") val basePlanVersion: Int,
)

@Serializable
data class RevisionRejectRequestDto(
    @SerialName("reason") val reason: String = "",
)
@Serializable
data class ProgressResponseDto(
    @SerialName("progress") val progress: ProgressDto,
    @SerialName("session") val session: SessionDto,
)

@Serializable
data class ConditionImpactDto(
    @SerialName("requires_regeneration") val requiresRegeneration: Boolean = false,
    @SerialName("requires_revision") val requiresRevision: Boolean = false,
    @SerialName("changed_fields") val changedFields: List<String> = emptyList(),
    @SerialName("message") val message: String = "",
)

@Serializable
data class ConditionsPatchResponseDto(
    @SerialName("session") val session: SessionDto,
    @SerialName("impact") val impact: ConditionImpactDto,
)

@Serializable
data class AskResponseDto(
    @SerialName("id") val id: String,
    @SerialName("question") val question: String,
    @SerialName("answer") val answer: String,
    @SerialName("citations") val citations: List<String> = emptyList(),
    @SerialName("limitations") val limitations: List<String> = emptyList(),
    @SerialName("created_at") val createdAt: String = "",
)

@Serializable
data class CompleteResponseDto(
    @SerialName("session") val session: SessionDto,
    @SerialName("outcome") val outcome: JsonObject? = null,
)

@Serializable
data class RevisionChangeDto(
    @SerialName("op") val op: String,
    @SerialName("step_id") val stepId: String? = null,
    @SerialName("before") val before: JsonObject? = null,
    @SerialName("after") val after: JsonObject? = null,
    @SerialName("reason") val reason: String = "",
)

@Serializable
data class RevisionDto(
    @SerialName("id") val id: String,
    @SerialName("session_id") val sessionId: String,
    @SerialName("trigger") val trigger: String,
    @SerialName("feedback_id") val feedbackId: String? = null,
    @SerialName("request_reason") val requestReason: String? = null,
    @SerialName("base_plan_version") val basePlanVersion: Int,
    @SerialName("status") val status: String,
    @SerialName("changes") val changes: List<RevisionChangeDto> = emptyList(),
    @SerialName("created_at") val createdAt: String = "",
    @SerialName("applied_at") val appliedAt: String? = null,
    @SerialName("rejected_at") val rejectedAt: String? = null,
)

@Serializable
data class RevisionApplyResponseDto(
    @SerialName("plan") val plan: PlanDto,
    @SerialName("revision") val revision: RevisionDto,
)

@Serializable
data class MediaDto(
    @SerialName("id") val id: String,
    @SerialName("kind") val kind: String,
    @SerialName("mime") val mime: String,
    @SerialName("size_bytes") val sizeBytes: Long,
    @SerialName("width") val width: Int,
    @SerialName("height") val height: Int,
    @SerialName("duration_s") val durationS: Double? = null,
    @SerialName("sha256") val sha256: String,
    @SerialName("status") val status: String,
    @SerialName("warnings") val warnings: List<String> = emptyList(),
    @SerialName("created_at") val createdAt: String = "",
)

@Serializable
data class ObservationEvidenceDto(
    @SerialName("media_id") val mediaId: String,
    @SerialName("kind") val kind: String,
    @SerialName("frame_index") val frameIndex: Int? = null,
    @SerialName("timestamp_s") val timestampS: Double? = null,
)

@Serializable
data class ObservationDto(
    @SerialName("text") val text: String,
    @SerialName("evidence") val evidence: ObservationEvidenceDto,
    @SerialName("certainty") val certainty: String,
)

@Serializable
data class MotionMetricsDto(
    @SerialName("method") val method: String,
    @SerialName("sample_fps") val sampleFps: Int,
    @SerialName("frame_count") val frameCount: Int,
    @SerialName("mean_translation_px") val meanTranslationPx: Double,
    @SerialName("p95_translation_px") val p95TranslationPx: Double,
    @SerialName("mean_rotation_deg") val meanRotationDeg: Double,
    @SerialName("direction_changes") val directionChanges: Int,
    @SerialName("limitations") val limitations: List<String> = emptyList(),
)

@Serializable
data class FeedbackAnalysisDto(
    @SerialName("summary") val summary: String,
    @SerialName("observations") val observations: List<ObservationDto> = emptyList(),
    @SerialName("assessment") val assessment: String,
    @SerialName("uncertainties") val uncertainties: List<String> = emptyList(),
    @SerialName("limitations") val limitations: List<String> = emptyList(),
    @SerialName("motion_metrics") val motionMetrics: MotionMetricsDto? = null,
    @SerialName("sampled_frame_timestamps_s") val sampledFrameTimestampsS: List<Double> = emptyList(),
    @SerialName("audio_analyzed") val audioAnalyzed: Boolean = false,
    @SerialName("audio_note") val audioNote: String = "",
)

@Serializable
data class FeedbackDto(
    @SerialName("id") val id: String,
    @SerialName("session_id") val sessionId: String,
    @SerialName("step_id") val stepId: String,
    @SerialName("plan_version") val planVersion: Int,
    @SerialName("media_ids") val mediaIds: List<String> = emptyList(),
    @SerialName("analysis") val analysis: FeedbackAnalysisDto,
    @SerialName("suggested_actions") val suggestedActions: List<String> = emptyList(),
    @SerialName("follow_up_questions") val followUpQuestions: List<String> = emptyList(),
    @SerialName("revision_id") val revisionId: String? = null,
    @SerialName("created_at") val createdAt: String = "",
)

@Serializable
data class FeedbackListDto(
    @SerialName("items") val items: List<FeedbackDto> = emptyList(),
    @SerialName("next_cursor") val nextCursor: String? = null,
)

@Serializable
data class FeedbackJobRequestDto(
    @SerialName("step_id") val stepId: String,
    @SerialName("plan_version") val planVersion: Int,
    @SerialName("media_ids") val mediaIds: List<String>,
    @SerialName("note") val note: String = "",
)
