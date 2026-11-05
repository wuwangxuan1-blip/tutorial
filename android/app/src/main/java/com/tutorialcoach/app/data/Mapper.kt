package com.tutorialcoach.app.data

import com.tutorialcoach.app.domain.DomainAdjustment
import com.tutorialcoach.app.domain.DomainCameraMoveSpec
import com.tutorialcoach.app.domain.DomainFeedback
import com.tutorialcoach.app.domain.DomainMedia
import com.tutorialcoach.app.domain.DomainMotionMetrics
import com.tutorialcoach.app.domain.DomainObservation
import com.tutorialcoach.app.domain.DomainObservationEvidence
import com.tutorialcoach.app.domain.DomainOrientationPath
import com.tutorialcoach.app.domain.DomainPlan
import com.tutorialcoach.app.domain.DomainPoint
import com.tutorialcoach.app.domain.DomainPositionPath
import com.tutorialcoach.app.domain.DomainPreparation
import com.tutorialcoach.app.domain.DomainProgress
import com.tutorialcoach.app.domain.DomainQuestion
import com.tutorialcoach.app.domain.DomainRecipe
import com.tutorialcoach.app.domain.DomainRecipeCompare
import com.tutorialcoach.app.domain.DomainRecipeIngredient
import com.tutorialcoach.app.domain.DomainRecipeStep
import com.tutorialcoach.app.domain.DomainRecipeVariables
import com.tutorialcoach.app.domain.DomainRecipeVersion
import com.tutorialcoach.app.domain.DomainRevision
import com.tutorialcoach.app.domain.DomainRevisionChange
import com.tutorialcoach.app.domain.DomainSession
import com.tutorialcoach.app.domain.DomainStep
import com.tutorialcoach.app.domain.DomainSubjectAnchor
import com.tutorialcoach.app.domain.DomainTasting
import com.tutorialcoach.app.domain.DomainTimer
import com.tutorialcoach.app.domain.DomainVariableDiff
import com.tutorialcoach.app.domain.DomainZoomSpec

import kotlinx.serialization.json.JsonElement
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
    visualAidType = visualAid?.type,
    cameraMove = visualAid?.cameraMove?.toDomain(),
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

fun MediaDto.toDomain(): DomainMedia = DomainMedia(
    id = id,
    kind = kind,
    mime = mime,
    sizeBytes = sizeBytes,
    width = width,
    height = height,
    durationS = durationS,
    sha256 = sha256,
    warnings = warnings,
)

fun ObservationEvidenceDto.toDomain(): DomainObservationEvidence = DomainObservationEvidence(
    mediaId = mediaId,
    kind = kind,
    frameIndex = frameIndex,
    timestampS = timestampS,
)

fun ObservationDto.toDomain(): DomainObservation = DomainObservation(
    text = text,
    evidence = evidence.toDomain(),
    certainty = certainty,
)

fun MotionMetricsDto.toDomain(): DomainMotionMetrics = DomainMotionMetrics(
    method = method,
    sampleFps = sampleFps,
    frameCount = frameCount,
    meanTranslationPx = meanTranslationPx,
    p95TranslationPx = p95TranslationPx,
    meanRotationDeg = meanRotationDeg,
    directionChanges = directionChanges,
    limitations = limitations,
)

fun FeedbackDto.toDomain(): DomainFeedback = DomainFeedback(
    id = id,
    sessionId = sessionId,
    stepId = stepId,
    planVersion = planVersion,
    mediaIds = mediaIds,
    summary = analysis.summary,
    observations = analysis.observations.map { it.toDomain() },
    assessment = analysis.assessment,
    uncertainties = analysis.uncertainties,
    limitations = analysis.limitations,
    motionMetrics = analysis.motionMetrics?.toDomain(),
    sampledFrameTimestampsS = analysis.sampledFrameTimestampsS,
    audioAnalyzed = analysis.audioAnalyzed,
    audioNote = analysis.audioNote,
    suggestedActions = suggestedActions,
    followUpQuestions = followUpQuestions,
    createdAt = createdAt,
)
fun PointDto.toDomain(): DomainPoint = DomainPoint(x, y)

fun SubjectAnchorDto.toDomain(): DomainSubjectAnchor = DomainSubjectAnchor(x, y, label)

fun PositionPathDto.toDomain(): DomainPositionPath = DomainPositionPath(
    space = space,
    start = start.toDomain(),
    end = end.toDomain(),
    control = control?.toDomain(),
    arc = arc,
)

fun OrientationPathDto.toDomain(): DomainOrientationPath = DomainOrientationPath(
    startYawDeg = startYawDeg,
    endYawDeg = endYawDeg,
    startPitchDeg = startPitchDeg,
    endPitchDeg = endPitchDeg,
)

fun ZoomSpecDto.toDomain(): DomainZoomSpec = DomainZoomSpec(startScale, endScale)

fun CameraMoveSpecDto.toDomain(): DomainCameraMoveSpec = DomainCameraMoveSpec(
    id = id,
    shotType = shotType,
    motionType = motionType,
    technique = technique,
    subjectAnchor = subjectAnchor.toDomain(),
    positionPath = positionPath?.toDomain(),
    orientationPath = orientationPath?.toDomain(),
    zoom = zoom?.toDomain(),
    durationS = durationS,
    easing = easing,
    aspectRatio = aspectRatio,
    notes = notes,
    limitations = limitations,
)

fun RecipeVariablesDto.toDomain(): DomainRecipeVariables = DomainRecipeVariables(
    doseG = doseG,
    waterG = waterG,
    ratio = ratio,
    waterTempC = waterTempC,
    grindSetting = grindSetting,
    brewTimeS = brewTimeS,
    milkMl = milkMl,
    iceG = iceG,
    sweetenerG = sweetenerG,
)

fun RecipeIngredientDto.toDomain(): DomainRecipeIngredient =
    DomainRecipeIngredient(name, amount, unit)

fun RecipeStepDto.toDomain(): DomainRecipeStep =
    DomainRecipeStep(id, order, instruction, durationS, target)

fun RecipeDto.toDomain(): DomainRecipe = DomainRecipe(
    id = id,
    sessionId = sessionId,
    version = version,
    name = name,
    brewer = brewer,
    method = method,
    servings = servings,
    variables = variables.toDomain(),
    ingredients = ingredients.map { it.toDomain() },
    steps = steps.map { it.toDomain() },
    sourcePlanVersion = sourcePlanVersion,
    createdAt = createdAt,
)

fun TastingDto.toDomain(): DomainTasting = DomainTasting(
    id = id,
    recipeId = recipeId,
    recipeVersion = recipeVersion,
    sourness = sourness,
    sweetness = sweetness,
    bitterness = bitterness,
    body = body,
    aroma = aroma,
    aftertaste = aftertaste,
    overall = overall,
    notes = notes,
    createdAt = createdAt,
)

fun AdjustmentDto.toDomain(): DomainAdjustment = DomainAdjustment(
    id = id,
    recipeId = recipeId,
    baseVersion = baseVersion,
    newVersion = newVersion,
    variable = variable,
    fromValue = fromValue.displayValue(),
    toValue = toValue.displayValue(),
    reason = reason,
    expectedEffect = expectedEffect,
    tastingId = tastingId,
    createdAt = createdAt,
)

fun RecipeVersionDto.toDomain(): DomainRecipeVersion = DomainRecipeVersion(
    recipeId = recipeId,
    version = version,
    name = name,
    variables = variables.toDomain(),
    createdAt = createdAt,
    tasting = tasting?.toDomain(),
    adjustment = adjustment?.toDomain(),
)

fun VariableDiffDto.toDomain(): DomainVariableDiff = DomainVariableDiff(
    variable = variable,
    baseValue = baseValue?.displayValue() ?: "",
    targetValue = targetValue?.displayValue() ?: "",
    delta = delta,
)

fun RecipeCompareDto.toDomain(): DomainRecipeCompare = DomainRecipeCompare(
    baseRecipeId = base.recipeId,
    baseVersion = base.version,
    targetRecipeId = target.recipeId,
    targetVersion = target.version,
    variableDiffs = variableDiffs.map { it.toDomain() },
    tastingDeltas = tastingComparison?.deltas,
    notes = notes,
)

private fun JsonElement.displayValue(): String = toString().trim('"')
