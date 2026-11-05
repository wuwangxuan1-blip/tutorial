package com.tutorialcoach.app.data

import com.tutorialcoach.app.domain.DomainAdjustment
import com.tutorialcoach.app.domain.DomainAnswer
import com.tutorialcoach.app.domain.DomainFeedback
import com.tutorialcoach.app.domain.DomainImpact
import com.tutorialcoach.app.domain.DomainPlan
import com.tutorialcoach.app.domain.DomainProgress
import com.tutorialcoach.app.domain.DomainRecipe
import com.tutorialcoach.app.domain.DomainRecipeCompare
import com.tutorialcoach.app.domain.DomainRecipeVersion
import com.tutorialcoach.app.domain.DomainRevision
import com.tutorialcoach.app.domain.DomainSession
import com.tutorialcoach.app.domain.DomainTasting
import java.io.File
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject

class SessionRepository(
    private val api: ApiClient,
    private val localStore: LocalStore,
) : PlanGateway, SessionActions, FeedbackGateway, RecipeGateway {
    private val _session = MutableStateFlow<DomainSession?>(null)
    override val session: StateFlow<DomainSession?> = _session.asStateFlow()

    private val _plan = MutableStateFlow<DomainPlan?>(null)
    override val plan: StateFlow<DomainPlan?> = _plan.asStateFlow()

    private val _progress = MutableStateFlow(DomainProgress())
    override val progress: StateFlow<DomainProgress> = _progress.asStateFlow()

    suspend fun createSession(goal: String, domain: String): DomainSession {
        val response = api.createSession(
            CreateSessionRequest(
                domain = domain,
                goal = goal,
                conditions = JsonObject(emptyMap()),
            ),
        )
        val mapped = response.toDomain()
        _session.value = mapped
        _plan.value = null
        _progress.value = mapped.progress
        localStore.saveSession(mapped)
        localStore.saveProgress(mapped.progress)
        return mapped
    }

    suspend fun submitAnswers(sessionId: String, answers: List<AnswerDto>): DomainSession {
        val response = api.submitAnswers(sessionId, answers)
        val mapped = response.toDomain()
        _session.value = mapped
        _progress.value = mapped.progress
        localStore.saveProgress(mapped.progress)
        return mapped
    }

    suspend fun restore(): Boolean {
        val sessionId = localStore.lastSessionId ?: return false
        return try {
            val restored = api.getSession(sessionId).toDomain()
            _session.value = restored
            _progress.value = restored.progress
            if (restored.currentPlanVersion != null) {
                _plan.value = api.getPlan(sessionId).toDomain()
            }
            localStore.saveProgress(restored.progress)
            true
        } catch (error: Exception) {
            if (error is CancellationException) throw error
            false
        }
    }

    override suspend fun createPlanJob(
        sessionId: String,
        basePlanVersion: Int?,
        idempotencyKey: String,
    ): JobDto = api.createPlanJob(sessionId, basePlanVersion, idempotencyKey)

    override suspend fun getJob(jobId: String): JobDto = api.getJob(jobId)

    override suspend fun uploadMedia(
        file: File,
        mime: String,
        kind: String,
        onProgress: (Float) -> Unit,
    ): MediaDto = api.uploadMedia(file, mime, kind, onProgress)

    override suspend fun createFeedbackJob(
        sessionId: String,
        request: FeedbackJobRequestDto,
        idempotencyKey: String,
    ): JobDto = api.createFeedbackJob(sessionId, request, idempotencyKey)

    override suspend fun getFeedback(feedbackId: String): DomainFeedback =
        api.getFeedback(feedbackId).toDomain()

    override suspend fun getEvidenceFrame(
        feedbackId: String,
        mediaId: String,
        frameIndex: Int,
        timestampS: Double,
    ): ByteArray? = api.getEvidenceFrame(feedbackId, mediaId, frameIndex, timestampS)

    override suspend fun listFeedback(
        sessionId: String,
        stepId: String?,
    ): List<DomainFeedback> = api.listFeedback(sessionId, stepId).map { it.toDomain() }

    override suspend fun createRecipe(
        sessionId: String,
        basePlanVersion: Int,
        demo: Boolean,
    ): DomainRecipe = api.createRecipe(sessionId, basePlanVersion, demo).toDomain()

    override suspend fun listRecipes(sessionId: String): List<DomainRecipe> =
        api.listRecipes(sessionId).map { it.toDomain() }

    override suspend fun getRecipe(recipeId: String): DomainRecipe =
        api.getRecipe(recipeId).toDomain()

    override suspend fun addTasting(
        recipeId: String,
        request: TastingRequestDto,
    ): DomainTasting = api.addTasting(recipeId, request).toDomain()

    override suspend fun adjustRecipe(
        recipeId: String,
        request: AdjustmentRequestDto,
    ): Pair<DomainRecipe, DomainAdjustment> {
        val response = api.adjustRecipe(recipeId, request)
        return response.recipe.toDomain() to response.adjustment.toDomain()
    }

    override suspend fun listRecipeHistory(recipeId: String): List<DomainRecipeVersion> =
        api.listRecipeHistory(recipeId).map { it.toDomain() }

    override suspend fun compareRecipes(
        recipeId: String,
        againstId: String,
    ): DomainRecipeCompare = api.compareRecipes(recipeId, againstId).toDomain()

    override suspend fun loadPlan(sessionId: String): DomainPlan {
        val mapped = api.getPlan(sessionId).toDomain()
        val current = _session.value
        if (current?.id == sessionId) {
            _plan.value = mapped
            if (current.currentPlanVersion != mapped.version) {
                _session.value = current.copy(currentPlanVersion = mapped.version)
            }
        }
        return mapped
    }

    override suspend fun updateProgress(
        sessionId: String,
        update: ProgressUpdate,
    ): DomainProgress {
        val response = api.updateProgress(sessionId, update)
        if (_session.value?.id == sessionId) {
            _session.value = response.session.toDomain()
        }
        val mapped = response.progress.toDomain()
        _progress.value = mapped
        localStore.saveProgress(mapped)
        return mapped
    }

    override suspend fun pauseSession(sessionId: String): DomainSession {
        val mapped = api.pauseSession(sessionId).toDomain()
        _session.value = mapped
        return mapped
    }

    override suspend fun resumeSession(sessionId: String): DomainSession {
        val mapped = api.resumeSession(sessionId).toDomain()
        _session.value = mapped
        return mapped
    }

    override suspend fun completeSession(
        sessionId: String,
        rating: Int?,
        notes: String,
    ): DomainSession {
        val response = api.completeSession(sessionId, rating, notes)
        val mapped = response.session.toDomain()
        _session.value = mapped
        return mapped
    }

    override suspend fun ask(
        sessionId: String,
        question: String,
        stepId: String,
        planVersion: Int,
    ): DomainAnswer {
        val response = api.ask(sessionId, question, stepId, planVersion)
        return DomainAnswer(
            id = response.id,
            question = response.question,
            answer = response.answer,
            citations = response.citations,
            limitations = response.limitations,
        )
    }

    override suspend fun patchConditions(
        sessionId: String,
        basePlanVersion: Int?,
        conditions: Map<String, JsonElement?>,
    ): DomainImpact {
        val response = api.patchConditions(sessionId, basePlanVersion, conditions)
        if (_session.value?.id == sessionId) {
            _session.value = response.session.toDomain()
        }
        return DomainImpact(
            requiresRegeneration = response.impact.requiresRegeneration,
            requiresRevision = response.impact.requiresRevision,
            changedFields = response.impact.changedFields,
            message = response.impact.message,
        )
    }

    override suspend fun createRevisionJob(
        sessionId: String,
        basePlanVersion: Int,
        requestReason: String,
        idempotencyKey: String,
    ): JobDto = api.createRevisionJob(sessionId, basePlanVersion, requestReason, idempotencyKey)

    override suspend fun listRevisions(sessionId: String): List<DomainRevision> =
        api.listRevisions(sessionId).map { it.toDomain() }

    override suspend fun applyRevision(
        sessionId: String,
        revisionId: String,
        basePlanVersion: Int,
    ): DomainPlan {
        val response = api.applyRevision(sessionId, revisionId, basePlanVersion)
        val plan = response.plan.toDomain()
        if (_session.value?.id == sessionId) {
            _plan.value = plan
            _session.value = _session.value?.copy(currentPlanVersion = plan.version)
        }
        return plan
    }

    override suspend fun rejectRevision(
        sessionId: String,
        revisionId: String,
        reason: String,
    ): DomainRevision = api.rejectRevision(sessionId, revisionId, reason).toDomain()

    suspend fun health(): HealthDto = api.health()

    suspend fun capabilities(): CapabilitiesDto = api.capabilities()

    fun clear() {
        _session.value = null
        _plan.value = null
        _progress.value = DomainProgress()
        localStore.clear()
    }
}