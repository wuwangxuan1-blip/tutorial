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
    @SerialName("visual_aid") val visualAid: VisualAidDto? = null,
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
data class PointDto(
    @SerialName("x") val x: Double,
    @SerialName("y") val y: Double,
)

@Serializable
data class SubjectAnchorDto(
    @SerialName("x") val x: Double,
    @SerialName("y") val y: Double,
    @SerialName("label") val label: String,
)

@Serializable
data class PositionPathDto(
    @SerialName("space") val space: String,
    @SerialName("start") val start: PointDto,
    @SerialName("end") val end: PointDto,
    @SerialName("control") val control: PointDto? = null,
    @SerialName("arc") val arc: String = "none",
)

@Serializable
data class OrientationPathDto(
    @SerialName("start_yaw_deg") val startYawDeg: Double,
    @SerialName("end_yaw_deg") val endYawDeg: Double,
    @SerialName("start_pitch_deg") val startPitchDeg: Double,
    @SerialName("end_pitch_deg") val endPitchDeg: Double,
)

@Serializable
data class ZoomSpecDto(
    @SerialName("start_scale") val startScale: Double,
    @SerialName("end_scale") val endScale: Double,
)

@Serializable
data class CameraMoveSpecDto(
    @SerialName("id") val id: String,
    @SerialName("shot_type") val shotType: String,
    @SerialName("motion_type") val motionType: String,
    @SerialName("technique") val technique: String,
    @SerialName("subject_anchor") val subjectAnchor: SubjectAnchorDto,
    @SerialName("position_path") val positionPath: PositionPathDto? = null,
    @SerialName("orientation_path") val orientationPath: OrientationPathDto? = null,
    @SerialName("zoom") val zoom: ZoomSpecDto? = null,
    @SerialName("duration_s") val durationS: Int,
    @SerialName("easing") val easing: String,
    @SerialName("aspect_ratio") val aspectRatio: String,
    @SerialName("notes") val notes: List<String> = emptyList(),
    @SerialName("limitations") val limitations: List<String> = emptyList(),
)

@Serializable
data class VisualAidDto(
    @SerialName("type") val type: String,
    @SerialName("camera_move") val cameraMove: CameraMoveSpecDto? = null,
)

@Serializable
data class RecipeVariablesDto(
    @SerialName("dose_g") val doseG: Double? = null,
    @SerialName("water_g") val waterG: Double? = null,
    @SerialName("ratio") val ratio: Double? = null,
    @SerialName("water_temp_c") val waterTempC: Double? = null,
    @SerialName("grind_setting") val grindSetting: String? = null,
    @SerialName("brew_time_s") val brewTimeS: Int? = null,
    @SerialName("milk_ml") val milkMl: Double? = null,
    @SerialName("ice_g") val iceG: Double? = null,
    @SerialName("sweetener_g") val sweetenerG: Double? = null,
)

@Serializable
data class RecipeIngredientDto(
    @SerialName("name") val name: String,
    @SerialName("amount") val amount: Double,
    @SerialName("unit") val unit: String,
)

@Serializable
data class RecipeStepDto(
    @SerialName("id") val id: String,
    @SerialName("order") val order: Int,
    @SerialName("instruction") val instruction: String,
    @SerialName("duration_s") val durationS: Int,
    @SerialName("target") val target: String,
)

@Serializable
data class RecipeDto(
    @SerialName("id") val id: String,
    @SerialName("session_id") val sessionId: String,
    @SerialName("version") val version: Int,
    @SerialName("name") val name: String,
    @SerialName("brewer") val brewer: String,
    @SerialName("method") val method: String,
    @SerialName("servings") val servings: Int,
    @SerialName("variables") val variables: RecipeVariablesDto,
    @SerialName("ingredients") val ingredients: List<RecipeIngredientDto> = emptyList(),
    @SerialName("steps") val steps: List<RecipeStepDto> = emptyList(),
    @SerialName("source_plan_version") val sourcePlanVersion: Int,
    @SerialName("created_at") val createdAt: String = "",
)

@Serializable
data class TastingDto(
    @SerialName("id") val id: String,
    @SerialName("recipe_id") val recipeId: String,
    @SerialName("recipe_version") val recipeVersion: Int,
    @SerialName("sourness") val sourness: Int,
    @SerialName("sweetness") val sweetness: Int,
    @SerialName("bitterness") val bitterness: Int,
    @SerialName("body") val body: Int,
    @SerialName("aroma") val aroma: Int,
    @SerialName("aftertaste") val aftertaste: Int,
    @SerialName("overall") val overall: Int,
    @SerialName("notes") val notes: String = "",
    @SerialName("created_at") val createdAt: String = "",
)

@Serializable
data class AdjustmentDto(
    @SerialName("id") val id: String,
    @SerialName("recipe_id") val recipeId: String,
    @SerialName("base_version") val baseVersion: Int,
    @SerialName("new_version") val newVersion: Int,
    @SerialName("variable") val variable: String,
    @SerialName("from_value") val fromValue: JsonElement,
    @SerialName("to_value") val toValue: JsonElement,
    @SerialName("reason") val reason: String,
    @SerialName("expected_effect") val expectedEffect: String = "",
    @SerialName("tasting_id") val tastingId: String? = null,
    @SerialName("created_at") val createdAt: String = "",
)

@Serializable
data class AdjustmentResponseDto(
    @SerialName("recipe") val recipe: RecipeDto,
    @SerialName("adjustment") val adjustment: AdjustmentDto,
)

@Serializable
data class RecipeVersionDto(
    @SerialName("recipe_id") val recipeId: String,
    @SerialName("version") val version: Int,
    @SerialName("name") val name: String,
    @SerialName("brewer") val brewer: String,
    @SerialName("method") val method: String,
    @SerialName("servings") val servings: Int,
    @SerialName("variables") val variables: RecipeVariablesDto,
    @SerialName("created_at") val createdAt: String = "",
    @SerialName("tasting") val tasting: TastingDto? = null,
    @SerialName("adjustment") val adjustment: AdjustmentDto? = null,
)

@Serializable
data class RecipeRefDto(
    @SerialName("recipe_id") val recipeId: String,
    @SerialName("version") val version: Int,
)

@Serializable
data class VariableDiffDto(
    @SerialName("variable") val variable: String,
    @SerialName("base_value") val baseValue: JsonElement? = null,
    @SerialName("target_value") val targetValue: JsonElement? = null,
    @SerialName("delta") val delta: Double? = null,
)

@Serializable
data class TastingComparisonDto(
    @SerialName("base_tasting_id") val baseTastingId: String,
    @SerialName("target_tasting_id") val targetTastingId: String,
    @SerialName("deltas") val deltas: Map<String, Int> = emptyMap(),
)

@Serializable
data class RecipeCompareDto(
    @SerialName("base") val base: RecipeRefDto,
    @SerialName("target") val target: RecipeRefDto,
    @SerialName("variable_diffs") val variableDiffs: List<VariableDiffDto> = emptyList(),
    @SerialName("tasting_comparison") val tastingComparison: TastingComparisonDto? = null,
    @SerialName("notes") val notes: List<String> = emptyList(),
)

@Serializable
data class RecipeCreateRequestDto(
    @SerialName("base_plan_version") val basePlanVersion: Int,
    @SerialName("demo") val demo: Boolean = false,
)

@Serializable
data class TastingRequestDto(
    @SerialName("sourness") val sourness: Int,
    @SerialName("sweetness") val sweetness: Int,
    @SerialName("bitterness") val bitterness: Int,
    @SerialName("body") val body: Int,
    @SerialName("aroma") val aroma: Int,
    @SerialName("aftertaste") val aftertaste: Int,
    @SerialName("overall") val overall: Int,
    @SerialName("notes") val notes: String = "",
)

@Serializable
data class AdjustmentRequestDto(
    @SerialName("base_version") val baseVersion: Int,
    @SerialName("variable") val variable: String,
    @SerialName("to_value") val toValue: JsonElement,
    @SerialName("reason") val reason: String,
    @SerialName("tasting_id") val tastingId: String? = null,
)

@Serializable
data class FeedbackJobRequestDto(
    @SerialName("step_id") val stepId: String,
    @SerialName("plan_version") val planVersion: Int,
    @SerialName("media_ids") val mediaIds: List<String>,
    @SerialName("note") val note: String = "",
)
