package com.tutorialcoach.app.data

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.serialization.json.JsonObject

class SessionRepository(
    private val api: ApiClient,
) : PlanGateway {
    private val _session = MutableStateFlow<com.tutorialcoach.app.domain.DomainSession?>(null)
    override val session: StateFlow<com.tutorialcoach.app.domain.DomainSession?> = _session.asStateFlow()

    private val _plan = MutableStateFlow<com.tutorialcoach.app.domain.DomainPlan?>(null)
    override val plan: StateFlow<com.tutorialcoach.app.domain.DomainPlan?> = _plan.asStateFlow()

    suspend fun createSession(goal: String, domain: String): com.tutorialcoach.app.domain.DomainSession {
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
        return mapped
    }

    suspend fun submitAnswers(sessionId: String, answers: List<AnswerDto>): com.tutorialcoach.app.domain.DomainSession {
        val response = api.submitAnswers(sessionId, answers)
        val mapped = response.toDomain()
        _session.value = mapped
        return mapped
    }

    override suspend fun createPlanJob(
        sessionId: String,
        basePlanVersion: Int?,
        idempotencyKey: String,
    ): JobDto = api.createPlanJob(sessionId, basePlanVersion, idempotencyKey)

    override suspend fun getJob(jobId: String): JobDto = api.getJob(jobId)

    override suspend fun loadPlan(sessionId: String): com.tutorialcoach.app.domain.DomainPlan {
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

    suspend fun health(): HealthDto = api.health()

    suspend fun capabilities(): CapabilitiesDto = api.capabilities()

    fun clear() {
        _session.value = null
        _plan.value = null
    }
}