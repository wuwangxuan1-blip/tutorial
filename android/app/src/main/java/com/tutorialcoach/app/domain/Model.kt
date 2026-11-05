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