package com.tutorialcoach.app.ui.screens.media

import com.tutorialcoach.app.data.ApiException
import com.tutorialcoach.app.data.ErrorDetailDto
import com.tutorialcoach.app.data.ErrorEnvelopeDto
import com.tutorialcoach.app.data.FeedbackGateway
import com.tutorialcoach.app.data.FeedbackJobRequestDto
import com.tutorialcoach.app.data.JobDto
import com.tutorialcoach.app.data.JobResultDto
import com.tutorialcoach.app.data.MediaDto
import com.tutorialcoach.app.data.SessionActions
import com.tutorialcoach.app.domain.DomainAnswer
import com.tutorialcoach.app.domain.DomainFeedback
import com.tutorialcoach.app.domain.DomainImpact
import com.tutorialcoach.app.domain.DomainObservation
import com.tutorialcoach.app.domain.DomainObservationEvidence
import com.tutorialcoach.app.domain.DomainPlan
import com.tutorialcoach.app.domain.DomainProgress
import com.tutorialcoach.app.domain.DomainRevision
import com.tutorialcoach.app.domain.DomainSession
import com.tutorialcoach.app.domain.DomainStep
import com.tutorialcoach.app.platform.MediaLoader
import com.tutorialcoach.app.platform.PreparedImage
import com.tutorialcoach.app.platform.PreparedVideo
import java.io.File
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class MediaViewModelTest {
    private val dispatcher = StandardTestDispatcher()

    @Before
    fun setUp() {
        Dispatchers.setMain(dispatcher)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    private fun step(id: String) = DomainStep(
        id = id,
        order = id.last().digitToInt(),
        phase = "execute",
        title = id,
        instruction = "instruction",
        why = "",
        durationS = 60,
        completionCriteria = listOf("标准"),
        safety = emptyList(),
        commonMistakes = emptyList(),
        evidenceHint = "",
        mediaPrompt = "",
    )

    private fun plan() = DomainPlan(
        id = "plan_1",
        sessionId = "sess_1",
        version = 1,
        domain = "photography",
        title = "环绕拍咖啡",
        summary = "",
        assumptions = emptyList(),
        preparation = emptyList(),
        steps = listOf(step("step_1"), step("step_2"), step("step_3")),
        totalEstimatedMin = 15,
        safetyNotes = emptyList(),
    )

    private fun session() = DomainSession(
        id = "sess_1",
        domain = "photography",
        goal = "环绕拍咖啡",
        status = "in_progress",
        questions = emptyList(),
        currentPlanVersion = 1,
    )

    private fun media(id: String, kind: String = "image") = MediaDto(
        id = id,
        kind = kind,
        mime = if (kind == "video") "video/mp4" else "image/jpeg",
        sizeBytes = 100,
        width = 100,
        height = 100,
        sha256 = "a".repeat(64),
        status = "ready",
    )

    private fun successJob(feedbackId: String) = JobDto(
        id = "job_1",
        type = "feedback_analysis",
        status = "succeeded",
        sessionId = "sess_1",
        result = JobResultDto(feedbackId = feedbackId),
    )

    private fun failedJob(code: String) = JobDto(
        id = "job_1",
        type = "feedback_analysis",
        status = "failed",
        sessionId = "sess_1",
        error = ErrorEnvelopeDto(
            ErrorDetailDto(code = code, message = "vision unavailable", retryable = false),
        ),
    )

    private fun feedback() = DomainFeedback(
        id = "fb_1",
        sessionId = "sess_1",
        stepId = "step_1",
        planVersion = 1,
        mediaIds = listOf("media_1"),
        summary = "画面可见。",
        observations = emptyList(),
        assessment = "unclear",
        uncertainties = emptyList(),
        limitations = listOf("单帧只能做定性观察。"),
        motionMetrics = null,
        sampledFrameTimestampsS = emptyList(),
        audioAnalyzed = false,
        audioNote = "本期不分析音频。",
        suggestedActions = emptyList(),
        followUpQuestions = emptyList(),
        createdAt = "2026-11-05T00:00:00Z",
    )

    private fun videoFeedback() = feedback().copy(
        mediaIds = listOf("media_1"),
        observations = listOf(
            DomainObservation(
                text = "第 0 秒画面可见主体。",
                evidence = DomainObservationEvidence(
                    mediaId = "media_1",
                    kind = "video_frame",
                    frameIndex = 0,
                    timestampS = 0.0,
                ),
                certainty = "high",
            ),
            DomainObservation(
                text = "第 2 秒画面可见主体。",
                evidence = DomainObservationEvidence(
                    mediaId = "media_1",
                    kind = "video_frame",
                    frameIndex = 2,
                    timestampS = 2.0,
                ),
                certainty = "high",
            ),
        ),
        sampledFrameTimestampsS = listOf(0.0, 1.0, 2.0),
    )

    private inner class FakeSessions : SessionActions {
        private val _session = MutableStateFlow<DomainSession?>(session())
        override val session: StateFlow<DomainSession?> = _session
        private val _plan = MutableStateFlow<DomainPlan?>(plan())
        override val plan: StateFlow<DomainPlan?> = _plan
        private val _progress = MutableStateFlow(
            DomainProgress(currentStepId = "step_1"),
        )
        override val progress: StateFlow<DomainProgress> = _progress

        override suspend fun loadPlan(sessionId: String): DomainPlan = plan()
        override suspend fun updateProgress(sessionId: String, update: com.tutorialcoach.app.data.ProgressUpdate): DomainProgress =
            _progress.value
        override suspend fun pauseSession(sessionId: String): DomainSession = session()
        override suspend fun resumeSession(sessionId: String): DomainSession = session()
        override suspend fun completeSession(sessionId: String, rating: Int?, notes: String): DomainSession = session()
        override suspend fun ask(sessionId: String, question: String, stepId: String, planVersion: Int): DomainAnswer =
            DomainAnswer("qa", question, "answer", emptyList(), emptyList())
        override suspend fun patchConditions(sessionId: String, basePlanVersion: Int?, conditions: Map<String, kotlinx.serialization.json.JsonElement?>): DomainImpact =
            DomainImpact(false, false, emptyList(), "")
        override suspend fun createRevisionJob(sessionId: String, basePlanVersion: Int, requestReason: String, idempotencyKey: String): JobDto =
            successJob("fb_1")
        override suspend fun getJob(jobId: String): JobDto = successJob("fb_1")
        override suspend fun listRevisions(sessionId: String): List<DomainRevision> = emptyList()
        override suspend fun applyRevision(sessionId: String, revisionId: String, basePlanVersion: Int): DomainPlan = plan()
        override suspend fun rejectRevision(sessionId: String, revisionId: String, reason: String): DomainRevision =
            throw UnsupportedOperationException()
    }

    private inner class FakeGateway : FeedbackGateway {
        var failUpload = false
        var job: JobDto = successJob("fb_1")
        var uploadCalls = 0
        var feedbackResult: DomainFeedback = feedback()
        var evidenceFrames: Map<String, ByteArray> = emptyMap()
        val frameRequests = mutableListOf<Triple<String, Int, Double>>()

        override suspend fun uploadMedia(
            file: File,
            mime: String,
            kind: String,
            onProgress: (Float) -> Unit,
        ): MediaDto {
            uploadCalls += 1
            if (failUpload) throw ApiException("MEDIA_DECODE_FAILED", "upload failed")
            onProgress(1f)
            return media("media_1", kind)
        }

        override suspend fun createFeedbackJob(
            sessionId: String,
            request: FeedbackJobRequestDto,
            idempotencyKey: String,
        ): JobDto = job

        override suspend fun getJob(jobId: String): JobDto = job
        override suspend fun getFeedback(feedbackId: String): DomainFeedback = feedbackResult

        override suspend fun getEvidenceFrame(
            feedbackId: String,
            mediaId: String,
            frameIndex: Int,
            timestampS: Double,
        ): ByteArray? {
            frameRequests += Triple(mediaId, frameIndex, timestampS)
            val key = evidenceFrameKey(mediaId, frameIndex, timestampS) ?: return null
            return evidenceFrames[key]
        }

        override suspend fun listFeedback(sessionId: String, stepId: String?): List<DomainFeedback> =
            listOf(feedback())
    }

    private inner class FakeLoader : MediaLoader {
        val savedEvidenceFrames = mutableListOf<ByteArray>()

        override fun prepareImage(uri: String): PreparedImage {
            val file = File.createTempFile("media_test_", ".jpg")
            file.writeBytes(ByteArray(100))
            return PreparedImage(uri, file, 100, 100)
        }

        override fun prepareVideo(uri: String): PreparedVideo {
            val file = File.createTempFile("media_video_", ".mp4")
            file.writeBytes(ByteArray(64))
            val thumbnail = File.createTempFile("media_thumb_", ".jpg")
            thumbnail.writeBytes(ByteArray(8))
            return PreparedVideo(
                uri = uri,
                file = file,
                durationMs = 2000L,
                sizeBytes = file.length(),
                thumbnail = thumbnail,
                mime = "video/mp4",
            )
        }

        override fun saveEvidenceFrame(data: ByteArray): File? {
            savedEvidenceFrames += data
            val file = File.createTempFile("media_frame_", ".jpg")
            file.writeBytes(data)
            return file
        }
    }

    @Test
    fun uploadFailureShowsErrorWithoutFakeFeedbackAndRetrySucceeds() = runTest(dispatcher) {
        val gateway = FakeGateway()
        gateway.failUpload = true
        val viewModel = MediaViewModel(FakeSessions(), gateway, FakeLoader(), dispatcher)
        viewModel.addImages(listOf("content://image/1"))
        viewModel.setPrivacyAccepted(true)

        viewModel.submit()
        advanceUntilIdle()

        assertTrue(viewModel.state.value.error != null)
        assertEquals(null, viewModel.state.value.feedback)
        assertEquals(1, gateway.uploadCalls)

        gateway.failUpload = false
        viewModel.retry()
        advanceUntilIdle()

        assertEquals(2, gateway.uploadCalls)
        assertTrue(viewModel.state.value.feedback != null)
        assertEquals("media_1", viewModel.state.value.uploaded["image_0"]?.id)
    }

    @Test
    fun visionUnavailableShowsExplicitErrorAndNoFakeFeedback() = runTest(dispatcher) {
        val gateway = FakeGateway()
        gateway.job = failedJob("VISION_UNSUPPORTED")
        val viewModel = MediaViewModel(FakeSessions(), gateway, FakeLoader(), dispatcher)
        viewModel.addImages(listOf("content://image/1"))
        viewModel.setPrivacyAccepted(true)

        viewModel.submit()
        advanceUntilIdle()

        assertTrue(viewModel.state.value.error?.contains("模型视觉不可用") == true)
        assertEquals(null, viewModel.state.value.feedback)
    }

    @Test
    fun videoEvidenceFramesUseServerProvidedBytesForEachObservation() = runTest(dispatcher) {
        val gateway = FakeGateway()
        gateway.feedbackResult = videoFeedback()
        gateway.evidenceFrames = mapOf(
            evidenceFrameKey("media_1", 0, 0.0)!! to "model-frame-0".toByteArray(),
            evidenceFrameKey("media_1", 2, 2.0)!! to "model-frame-2".toByteArray(),
        )
        val loader = FakeLoader()
        val viewModel = MediaViewModel(FakeSessions(), gateway, loader, dispatcher)
        viewModel.setVideo("content://video/1")
        viewModel.setPrivacyAccepted(true)

        viewModel.submit()
        advanceUntilIdle()

        assertEquals(
            listOf(Triple("media_1", 0, 0.0), Triple("media_1", 2, 2.0)),
            gateway.frameRequests,
        )
        assertEquals(2, loader.savedEvidenceFrames.size)
        val state = viewModel.state.value
        val first = state.evidenceFrameFile("media_1", 0, 0.0)
        val second = state.evidenceFrameFile("media_1", 2, 2.0)
        assertNotNull(first)
        assertNotNull(second)
        assertEquals("model-frame-0", first!!.readText())
        assertEquals("model-frame-2", second!!.readText())
        assertNotEquals(first.absolutePath, second.absolutePath)
        assertNull(state.evidenceFrameFile("media_1", 1, 1.0))
    }

    @Test
    fun missingEvidenceFrameIsUnavailableWithoutVideoThumbnailFallback() = runTest(dispatcher) {
        val gateway = FakeGateway()
        gateway.feedbackResult = videoFeedback()
        val loader = FakeLoader()
        val viewModel = MediaViewModel(FakeSessions(), gateway, loader, dispatcher)
        viewModel.setVideo("content://video/1")
        viewModel.setPrivacyAccepted(true)

        viewModel.submit()
        advanceUntilIdle()

        val state = viewModel.state.value
        assertNotNull(state.video?.thumbnail)
        assertTrue(state.evidenceFrames.isEmpty())
        assertTrue(loader.savedEvidenceFrames.isEmpty())
        assertNull(state.evidenceFrameFile("media_1", 0, 0.0))
        assertNull(state.evidenceFrameFile("media_1", 2, 2.0))
    }
}