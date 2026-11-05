package com.tutorialcoach.app.domain

data class DomainSession(
    val id: String,
    val domain: String,
    val goal: String,
    val status: String,
    val questions: List<DomainQuestion>,
    val currentPlanVersion: Int?,
    val progress: DomainProgress = DomainProgress(),
    val conditions: Map<String, String> = emptyMap(),
)

data class DomainProgress(
    val currentStepId: String? = null,
    val stepStatuses: Map<String, String> = emptyMap(),
    val evidenceLevels: Map<String, String> = emptyMap(),
    val timer: DomainTimer? = null,
    val updatedAt: String = "",
)

data class DomainTimer(
    val stepId: String,
    val state: String,
    val durationS: Int,
    val remainingS: Int,
    val anchorElapsedMs: Long?,
    val savedAtEpochMs: Long,
    val updatedAt: String,
)

data class DomainImpact(
    val requiresRegeneration: Boolean,
    val requiresRevision: Boolean,
    val changedFields: List<String>,
    val message: String,
)

data class DomainAnswer(
    val id: String,
    val question: String,
    val answer: String,
    val citations: List<String>,
    val limitations: List<String>,
)

data class DomainRevisionChange(
    val op: String,
    val stepId: String?,
    val before: Map<String, String>,
    val after: Map<String, String>,
    val reason: String,
)

data class DomainRevision(
    val id: String,
    val sessionId: String,
    val status: String,
    val requestReason: String?,
    val basePlanVersion: Int,
    val changes: List<DomainRevisionChange>,
    val createdAt: String,
)

data class DomainQuestion(
    val id: String,
    val field: String,
    val prompt: String,
    val kind: String,
    val required: Boolean,
    val options: List<String>,
    val unit: String?,
    val help: String,
)

data class DomainPreparation(
    val id: String,
    val text: String,
    val optional: Boolean,
)

data class DomainStep(
    val id: String,
    val order: Int,
    val phase: String,
    val title: String,
    val instruction: String,
    val why: String,
    val durationS: Int,
    val completionCriteria: List<String>,
    val safety: List<String>,
    val commonMistakes: List<String>,
    val evidenceHint: String,
    val mediaPrompt: String,
    val visualAidType: String? = null,
    val cameraMove: DomainCameraMoveSpec? = null,
)

data class DomainPlan(
    val id: String,
    val sessionId: String,
    val version: Int,
    val domain: String,
    val title: String,
    val summary: String,
    val assumptions: List<String>,
    val preparation: List<DomainPreparation>,
    val steps: List<DomainStep>,
    val totalEstimatedMin: Int,
    val safetyNotes: List<String>,
)

data class DomainMedia(
    val id: String,
    val kind: String,
    val mime: String,
    val sizeBytes: Long,
    val width: Int,
    val height: Int,
    val durationS: Double?,
    val sha256: String,
    val warnings: List<String> = emptyList(),
)

data class DomainObservationEvidence(
    val mediaId: String,
    val kind: String,
    val frameIndex: Int?,
    val timestampS: Double?,
)

data class DomainObservation(
    val text: String,
    val evidence: DomainObservationEvidence,
    val certainty: String,
)

data class DomainMotionMetrics(
    val method: String,
    val sampleFps: Int,
    val frameCount: Int,
    val meanTranslationPx: Double,
    val p95TranslationPx: Double,
    val meanRotationDeg: Double,
    val directionChanges: Int,
    val limitations: List<String>,
)

data class DomainFeedback(
    val id: String,
    val sessionId: String,
    val stepId: String,
    val planVersion: Int,
    val mediaIds: List<String>,
    val summary: String,
    val observations: List<DomainObservation>,
    val assessment: String,
    val uncertainties: List<String>,
    val limitations: List<String>,
    val motionMetrics: DomainMotionMetrics?,
    val sampledFrameTimestampsS: List<Double>,
    val audioAnalyzed: Boolean,
    val audioNote: String,
    val suggestedActions: List<String>,
    val followUpQuestions: List<String>,
    val createdAt: String,
)
data class DomainPoint(
    val x: Double,
    val y: Double,
)

data class DomainSubjectAnchor(
    val x: Double,
    val y: Double,
    val label: String,
)

data class DomainPositionPath(
    val space: String,
    val start: DomainPoint,
    val end: DomainPoint,
    val control: DomainPoint?,
    val arc: String,
)

data class DomainOrientationPath(
    val startYawDeg: Double,
    val endYawDeg: Double,
    val startPitchDeg: Double,
    val endPitchDeg: Double,
)

data class DomainZoomSpec(
    val startScale: Double,
    val endScale: Double,
)

data class DomainCameraMoveSpec(
    val id: String,
    val shotType: String,
    val motionType: String,
    val technique: String,
    val subjectAnchor: DomainSubjectAnchor,
    val positionPath: DomainPositionPath?,
    val orientationPath: DomainOrientationPath?,
    val zoom: DomainZoomSpec?,
    val durationS: Int,
    val easing: String,
    val aspectRatio: String,
    val notes: List<String>,
    val limitations: List<String>,
)

data class DomainRecipeVariables(
    val doseG: Double? = null,
    val waterG: Double? = null,
    val ratio: Double? = null,
    val waterTempC: Double? = null,
    val grindSetting: String? = null,
    val brewTimeS: Int? = null,
    val milkMl: Double? = null,
    val iceG: Double? = null,
    val sweetenerG: Double? = null,
) {
    fun entries(): List<Pair<String, String>> = buildList {
        doseG?.let { add("咖啡粉" to "${formatNumber(it)} g") }
        waterG?.let { add("水" to "${formatNumber(it)} g") }
        ratio?.let { add("粉水比" to "1:${formatNumber(it)}") }
        waterTempC?.let { add("水温" to "${formatNumber(it)} °C") }
        grindSetting?.let { add("研磨" to it) }
        brewTimeS?.let { add("总时长" to "${it} 秒") }
        milkMl?.let { add("牛奶" to "${formatNumber(it)} ml") }
        iceG?.let { add("冰" to "${formatNumber(it)} g") }
        sweetenerG?.let { add("甜味剂" to "${formatNumber(it)} g") }
    }

    private fun formatNumber(value: Double): String =
        if (value == value.toLong().toDouble()) value.toLong().toString() else value.toString()
}

data class DomainRecipeIngredient(
    val name: String,
    val amount: Double,
    val unit: String,
)

data class DomainRecipeStep(
    val id: String,
    val order: Int,
    val instruction: String,
    val durationS: Int,
    val target: String,
)

data class DomainRecipe(
    val id: String,
    val sessionId: String,
    val version: Int,
    val name: String,
    val brewer: String,
    val method: String,
    val servings: Int,
    val variables: DomainRecipeVariables,
    val ingredients: List<DomainRecipeIngredient>,
    val steps: List<DomainRecipeStep>,
    val sourcePlanVersion: Int,
    val createdAt: String,
)

data class DomainTasting(
    val id: String,
    val recipeId: String,
    val recipeVersion: Int,
    val sourness: Int,
    val sweetness: Int,
    val bitterness: Int,
    val body: Int,
    val aroma: Int,
    val aftertaste: Int,
    val overall: Int,
    val notes: String,
    val createdAt: String,
)

data class DomainAdjustment(
    val id: String,
    val recipeId: String,
    val baseVersion: Int,
    val newVersion: Int,
    val variable: String,
    val fromValue: String,
    val toValue: String,
    val reason: String,
    val expectedEffect: String,
    val tastingId: String?,
    val createdAt: String,
)

data class DomainRecipeVersion(
    val recipeId: String,
    val version: Int,
    val name: String,
    val variables: DomainRecipeVariables,
    val createdAt: String,
    val tasting: DomainTasting?,
    val adjustment: DomainAdjustment?,
)

data class DomainVariableDiff(
    val variable: String,
    val baseValue: String,
    val targetValue: String,
    val delta: Double?,
)

data class DomainRecipeCompare(
    val baseRecipeId: String,
    val baseVersion: Int,
    val targetRecipeId: String,
    val targetVersion: Int,
    val variableDiffs: List<DomainVariableDiff>,
    val tastingDeltas: Map<String, Int>?,
    val notes: List<String>,
)
