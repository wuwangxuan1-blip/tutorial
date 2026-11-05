package com.tutorialcoach.app.data

import com.tutorialcoach.app.domain.DomainFeedback
import java.io.File

interface FeedbackGateway {
    suspend fun uploadMedia(
        file: File,
        mime: String,
        kind: String,
        onProgress: (Float) -> Unit,
    ): MediaDto

    suspend fun createFeedbackJob(
        sessionId: String,
        request: FeedbackJobRequestDto,
        idempotencyKey: String,
    ): JobDto

    suspend fun getJob(jobId: String): JobDto

    suspend fun getFeedback(feedbackId: String): DomainFeedback

    suspend fun listFeedback(sessionId: String, stepId: String? = null): List<DomainFeedback>
}