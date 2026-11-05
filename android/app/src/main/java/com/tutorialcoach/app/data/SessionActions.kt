package com.tutorialcoach.app.data

import com.tutorialcoach.app.domain.DomainAnswer
import com.tutorialcoach.app.domain.DomainImpact
import com.tutorialcoach.app.domain.DomainPlan
import com.tutorialcoach.app.domain.DomainProgress
import com.tutorialcoach.app.domain.DomainRevision
import com.tutorialcoach.app.domain.DomainSession
import kotlinx.coroutines.flow.StateFlow
import kotlinx.serialization.json.JsonElement

interface SessionActions {
    val session: StateFlow<DomainSession?>
    val plan: StateFlow<DomainPlan?>
    val progress: StateFlow<DomainProgress>

    suspend fun loadPlan(sessionId: String): DomainPlan

    suspend fun updateProgress(sessionId: String, update: ProgressUpdate): DomainProgress

    suspend fun pauseSession(sessionId: String): DomainSession

    suspend fun resumeSession(sessionId: String): DomainSession

    suspend fun completeSession(sessionId: String, rating: Int?, notes: String): DomainSession

    suspend fun ask(
        sessionId: String,
        question: String,
        stepId: String,
        planVersion: Int,
    ): DomainAnswer

    suspend fun patchConditions(
        sessionId: String,
        basePlanVersion: Int?,
        conditions: Map<String, JsonElement?>,
    ): DomainImpact

    suspend fun createRevisionJob(
        sessionId: String,
        basePlanVersion: Int,
        requestReason: String,
        idempotencyKey: String,
    ): JobDto

    suspend fun getJob(jobId: String): JobDto

    suspend fun listRevisions(sessionId: String): List<DomainRevision>

    suspend fun applyRevision(
        sessionId: String,
        revisionId: String,
        basePlanVersion: Int,
    ): DomainPlan

    suspend fun rejectRevision(
        sessionId: String,
        revisionId: String,
        reason: String,
    ): DomainRevision
}