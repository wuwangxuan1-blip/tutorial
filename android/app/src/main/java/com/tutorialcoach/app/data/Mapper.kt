package com.tutorialcoach.app.data

import com.tutorialcoach.app.domain.DomainPlan
import com.tutorialcoach.app.domain.DomainPreparation
import com.tutorialcoach.app.domain.DomainQuestion
import com.tutorialcoach.app.domain.DomainSession
import com.tutorialcoach.app.domain.DomainStep

fun SessionDto.toDomain(): DomainSession = DomainSession(
    id = id,
    domain = domain,
    goal = goal,
    status = status,
    questions = questions.map { it.toDomain() },
    currentPlanVersion = currentPlanVersion,
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