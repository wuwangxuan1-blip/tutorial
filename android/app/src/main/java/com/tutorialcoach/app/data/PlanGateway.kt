package com.tutorialcoach.app.data

import com.tutorialcoach.app.domain.DomainPlan
import com.tutorialcoach.app.domain.DomainSession
import kotlinx.coroutines.flow.StateFlow

interface PlanGateway {
    val session: StateFlow<DomainSession?>
    val plan: StateFlow<DomainPlan?>

    suspend fun createPlanJob(
        sessionId: String,
        basePlanVersion: Int?,
        idempotencyKey: String,
    ): JobDto

    suspend fun getJob(jobId: String): JobDto

    suspend fun loadPlan(sessionId: String): DomainPlan
}