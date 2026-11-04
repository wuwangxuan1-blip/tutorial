package com.tutorialcoach.app.domain

data class DomainSession(
    val id: String,
    val domain: String,
    val goal: String,
    val status: String,
    val questions: List<DomainQuestion>,
    val currentPlanVersion: Int?,
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