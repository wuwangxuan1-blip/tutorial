package com.tutorialcoach.app.data

import com.tutorialcoach.app.domain.DomainPlan
import com.tutorialcoach.app.domain.DomainPreparation
import com.tutorialcoach.app.domain.DomainProgress
import com.tutorialcoach.app.domain.DomainQuestion
import com.tutorialcoach.app.domain.DomainRevision
import com.tutorialcoach.app.domain.DomainRevisionChange
import com.tutorialcoach.app.domain.DomainSession
import com.tutorialcoach.app.domain.DomainStep
import com.tutorialcoach.app.domain.DomainTimer

import kotlinx.serialization.json.JsonObject

fun SessionDto.toDomain(): DomainSession = DomainSession(
    id = id,
    domain = domain,
    goal = goal,
    status = status,
    questions = questions.map { it.toDomain() },
    currentPlanVersion = currentPlanVersion,
    progress = progress.toDomain(),
    conditions = conditions.toFlatMap(),
)

fun QuestionDto.toDomain(): DomainQuestion = DomainQuestion(
    id = id,
    field = field,
    prompt = prompt,
    kind = kind,
    required = required,
    options = options,
    unit = unit,
    help = help,
)

fun ProgressDto.toDomain(): DomainProgress = DomainProgress(
    currentStepId = currentStepId,
    stepStatuses = stepStatuses,
    evidenceLevels = evidenceLevels,
    timer = timer?.toDomain(),
    updatedAt = updatedAt,
)

fun TimerDto.toDomain(): DomainTimer = DomainTimer(
    stepId = stepId,
    state = state,
    durationS = durationS,
    remainingS = remainingS,
    anchorElapsedMs = anchorElapsedMs,
    savedAtEpochMs = savedAtEpochMs,
    updatedAt = updatedAt,
)

fun DomainTimer.toDto(): TimerDto = TimerDto(
    stepId = stepId,
    state = state,
    durationS = durationS,
    remainingS = remainingS,
    anchorElapsedMs = anchorElapsedMs,
    savedAtEpochMs = savedAtEpochMs,
    updatedAt = updatedAt,
)

fun PlanDto.toDomain(): DomainPlan = DomainPlan(
    id = id,
    sessionId = sessionId,
    version = version,
    domain = domain,
    title = title,
    summary = summary,
    assumptions = assumptions,
    preparation = preparation.map { it.toDomain() },
    steps = steps.map { it.toDomain() },
    totalEstimatedMin = totalEstimatedMin,
    safetyNotes = safetyNotes,
)

fun PreparationDto.toDomain(): DomainPreparation = DomainPreparation(
    id = id,
    text = text,
    optional = optional,
)

fun StepDto.toDomain(): DomainStep = DomainStep(
    id = id,
    order = order,
    phase = phase,
    title = title,
    instruction = instruction,
    why = why,
    durationS = durationS,
    completionCriteria = completionCriteria,
    safety = safety,
    commonMistakes = commonMistakes,
    evidenceHint = evidenceHint,
    mediaPrompt = mediaPrompt,
)

fun RevisionDto.toDomain(): DomainRevision = DomainRevision(
    id = id,
    sessionId = sessionId,
    status = status,
    requestReason = requestReason,
    basePlanVersion = basePlanVersion,
    changes = changes.map { it.toDomain() },
    createdAt = createdAt,
)

fun RevisionChangeDto.toDomain(): DomainRevisionChange = DomainRevisionChange(
    op = op,
    stepId = stepId,
    before = before?.toFlatMap() ?: emptyMap(),
    after = after?.toFlatMap() ?: emptyMap(),
    reason = reason,
)

private fun JsonObject.toFlatMap(): Map<String, String> = entries.associate { (key, value) ->
    key to value.toString().trim('"')
}