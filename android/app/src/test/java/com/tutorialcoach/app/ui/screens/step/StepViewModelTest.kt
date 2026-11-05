package com.tutorialcoach.app.ui.screens.step

import com.tutorialcoach.app.data.JobDto
import com.tutorialcoach.app.data.ProgressCache
import com.tutorialcoach.app.data.ProgressUpdate
import com.tutorialcoach.app.data.SessionActions
import com.tutorialcoach.app.data.toDomain
import com.tutorialcoach.app.domain.DomainAnswer
import com.tutorialcoach.app.domain.DomainImpact
import com.tutorialcoach.app.domain.DomainPlan
import com.tutorialcoach.app.domain.DomainProgress
import com.tutorialcoach.app.domain.DomainRevision
import com.tutorialcoach.app.domain.DomainSession
import com.tutorialcoach.app.domain.DomainStep
import com.tutorialcoach.app.domain.DomainTimer
import com.tutorialcoach.app.domain.TimerEngine
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.withContext
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceTimeBy
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class StepViewModelTest {
    private val dispatcher = StandardTestDispatcher()

    @Before
    fun setUp() {
        Dispatchers.setMain(dispatcher)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    private fun makeStep(order: Int) = DomainStep(
        id = "step_$order",
        order = order,
        phase = "execute",
        title = "步骤 $order",
        instruction = "执行步骤 $order。",
        why = "原因",
        durationS = 60,
        completionCriteria = listOf("可观察标准"),
        safety = emptyList(),
        commonMistakes = emptyList(),
        evidenceHint = "",
        mediaPrompt = "",
    )

    private fun makePlan() = DomainPlan(
        id = "plan_1",
        sessionId = "sess_1",
        version = 1,
        domain = "cooking",
        title = "番茄鸡蛋面",
        summary = "",
        assumptions = emptyList(),
        preparation = emptyList(),
        steps = listOf(makeStep(1), makeStep(2), makeStep(3)),
        totalEstimatedMin = 30,
        safetyNotes = emptyList(),
    )

    private fun makeSession() = DomainSession(
        id = "sess_1",
        domain = "cooking",
        goal = "番茄鸡蛋面",
        status = "in_progress",
        questions = emptyList(),
        currentPlanVersion = 1,
    )

    private inner class FakeGateway(
        private val initialProgress: DomainProgress = DomainProgress(),
    ) : SessionActions {
        private val _session = MutableStateFlow<DomainSession?>(makeSession())
        override val session: StateFlow<DomainSession?> = _session
        private val _plan = MutableStateFlow<DomainPlan?>(makePlan())
        override val plan: StateFlow<DomainPlan?> = _plan
        private val _progress = MutableStateFlow(initialProgress)
        override val progress: StateFlow<DomainProgress> = _progress

        var failUpdates = false
        val updates = mutableListOf<ProgressUpdate>()
        var blockFinishedPatch = false
        var finishedPatchGate: CompletableDeferred<Unit>? = null
        var blockFailingPatch = false
        var failingPatchGate: CompletableDeferred<Unit>? = null

        override suspend fun updateProgress(
            sessionId: String,
            update: ProgressUpdate,
        ): DomainProgress {
            if (failUpdates) {
                if (blockFailingPatch) {
                    val gate = CompletableDeferred<Unit>()
                    failingPatchGate = gate
                    withContext(NonCancellable) { gate.await() }
                }
                throw RuntimeException("progress patch rejected")
            }
            if (blockFinishedPatch && update.timer?.state == "finished") {
                val gate = CompletableDeferred<Unit>()
                finishedPatchGate = gate
                withContext(NonCancellable) { gate.await() }
            }
            updates += update
            val current = if (update.includeCurrentStep) {
                update.currentStepId
            } else {
                _progress.value.currentStepId
            }
            val statuses = _progress.value.stepStatuses.toMutableMap().apply {
                update.stepStatuses?.let { putAll(it) }
            }
            val evidences = _progress.value.evidenceLevels.toMutableMap().apply {
                update.evidenceLevels?.let { putAll(it) }
            }
            val timer = if (update.includeTimer) update.timer?.toDomain() else _progress.value.timer
            val next = DomainProgress(current, statuses, evidences, timer, "now")
            _progress.value = next
            return next
        }

        override suspend fun loadPlan(sessionId: String): DomainPlan = makePlan()

        override suspend fun pauseSession(sessionId: String): DomainSession = makeSession()

        override suspend fun resumeSession(sessionId: String): DomainSession = makeSession()

        override suspend fun completeSession(
            sessionId: String,
            rating: Int?,
            notes: String,
        ): DomainSession = makeSession()

        override suspend fun ask(
            sessionId: String,
            question: String,
            stepId: String,
            planVersion: Int,
        ): DomainAnswer = DomainAnswer("qa_1", question, "可以。", emptyList(), emptyList())

        override suspend fun patchConditions(
            sessionId: String,
            basePlanVersion: Int?,
            conditions: Map<String, kotlinx.serialization.json.JsonElement?>,
        ): DomainImpact = DomainImpact(false, false, emptyList(), "ok")

        override suspend fun createRevisionJob(
            sessionId: String,
            basePlanVersion: Int,
            requestReason: String,
            idempotencyKey: String,
        ): JobDto = throw UnsupportedOperationException()

        override suspend fun getJob(jobId: String): JobDto = throw UnsupportedOperationException()

        override suspend fun listRevisions(sessionId: String): List<DomainRevision> = emptyList()

        override suspend fun applyRevision(
            sessionId: String,
            revisionId: String,
            basePlanVersion: Int,
        ): DomainPlan = makePlan()

        override suspend fun rejectRevision(
            sessionId: String,
            revisionId: String,
            reason: String,
        ): DomainRevision = throw UnsupportedOperationException()
    }

    private inner class FakeCache : ProgressCache {
        var stepId: String? = null
        var timer: DomainTimer? = null

        override fun saveProgress(progress: DomainProgress) {
            stepId = progress.currentStepId
            timer = progress.timer
        }

        override fun currentStepId(): String? = stepId

        override fun loadTimer(): DomainTimer? = timer
    }

    @Test
    fun completeStepIsSelfReportedAndAdvances() = runTest(dispatcher) {
        val gateway = FakeGateway()
        val viewModel = StepViewModel(gateway, FakeCache(), TimerEngine { 0L }, { 1_000L })
        runCurrent()

        viewModel.completeStep()
        runCurrent()

        val done = gateway.updates.firstOrNull {
            it.stepStatuses?.get("step_1") == "done"
        }
        assertTrue(done != null)
        assertEquals("self_reported", done?.evidenceLevels?.get("step_1"))
        assertEquals(1, viewModel.state.value.index)
    }

    @Test
    fun invalidTimerAnchorRequiresConfirmation() = runTest(dispatcher) {
        val timer = DomainTimer(
            stepId = "step_1",
            state = "running",
            durationS = 300,
            remainingS = 200,
            anchorElapsedMs = 100L,
            savedAtEpochMs = 1_000L,
            updatedAt = "2026-11-05T00:00:00Z",
        )
        val gateway = FakeGateway(
            initialProgress = DomainProgress(
                currentStepId = "step_1",
                stepStatuses = mapOf("step_1" to "in_progress"),
                evidenceLevels = mapOf("step_1" to "none"),
                timer = timer,
                updatedAt = "2026-11-05T00:00:00Z",
            ),
        )
        val viewModel = StepViewModel(gateway, FakeCache(), TimerEngine { 50L }, { 1_000L })
        runCurrent()

        assertTrue(viewModel.state.value.timerNeedsConfirmation)
        assertEquals("paused", viewModel.state.value.timer?.state)
        assertEquals(200, viewModel.state.value.timerRemainingS)
    }

    @Test
    fun completeStepKeepsDoneNextStepAndUsesSinglePatch() = runTest(dispatcher) {
        val gateway = FakeGateway(
            initialProgress = DomainProgress(
                currentStepId = "step_1",
                stepStatuses = mapOf("step_1" to "in_progress", "step_2" to "done"),
                evidenceLevels = mapOf("step_2" to "self_reported"),
            ),
        )
        val viewModel = StepViewModel(gateway, FakeCache(), TimerEngine { 0L }, { 1_000L })
        runCurrent()

        viewModel.completeStep()
        runCurrent()

        assertEquals(1, gateway.updates.size)
        val update = gateway.updates.single()
        assertEquals("done", update.stepStatuses?.get("step_1"))
        assertEquals("self_reported", update.evidenceLevels?.get("step_1"))
        assertTrue(update.stepStatuses?.containsKey("step_2") != true)
        assertEquals("step_2", update.currentStepId)
        assertEquals(1, viewModel.state.value.index)
        assertEquals("done", gateway.progress.value.stepStatuses["step_2"])
        assertEquals("self_reported", gateway.progress.value.evidenceLevels["step_2"])
    }

    @Test
    fun skipStepKeepsSkippedNextStepAndUsesSinglePatch() = runTest(dispatcher) {
        val gateway = FakeGateway(
            initialProgress = DomainProgress(
                currentStepId = "step_1",
                stepStatuses = mapOf("step_1" to "in_progress", "step_2" to "skipped"),
                evidenceLevels = mapOf("step_2" to "none"),
            ),
        )
        val viewModel = StepViewModel(gateway, FakeCache(), TimerEngine { 0L }, { 1_000L })
        runCurrent()

        viewModel.skipStep()
        runCurrent()

        assertEquals(1, gateway.updates.size)
        val update = gateway.updates.single()
        assertEquals("skipped", update.stepStatuses?.get("step_1"))
        assertTrue(update.stepStatuses?.containsKey("step_2") != true)
        assertEquals(1, viewModel.state.value.index)
        assertEquals("skipped", gateway.progress.value.stepStatuses["step_2"])
    }

    @Test
    fun completeStepFailureDoesNotAdvance() = runTest(dispatcher) {
        val gateway = FakeGateway()
        gateway.failUpdates = true
        val viewModel = StepViewModel(gateway, FakeCache(), TimerEngine { 0L }, { 1_000L })
        runCurrent()

        viewModel.completeStep()
        runCurrent()

        assertEquals(0, viewModel.state.value.index)
        assertTrue(viewModel.state.value.error != null)
        assertEquals(0, gateway.updates.size)
    }

    @Test
    fun resetAfterNaturalFinishRestartsTicker() = runTest(dispatcher) {
        val gateway = FakeGateway()
        val viewModel = StepViewModel(
            gateway,
            FakeCache(),
            TimerEngine { testScheduler.currentTime },
            { testScheduler.currentTime },
        )
        runCurrent()

        viewModel.startTimer()
        runCurrent()
        advanceTimeBy(60_000)
        runCurrent()
        assertEquals("finished", viewModel.state.value.timer?.state)
        assertEquals(0, viewModel.state.value.timerRemainingS)

        viewModel.resetTimer()
        runCurrent()
        assertEquals("running", viewModel.state.value.timer?.state)
        advanceTimeBy(5_000)
        runCurrent()
        assertTrue(viewModel.state.value.timerRemainingS < 60)

        viewModel.pauseTimer()
        runCurrent()
        advanceTimeBy(1_000)
        runCurrent()
    }

    @Test
    fun confirmTimerResetRestartsTicker() = runTest(dispatcher) {
        val invalidTimer = DomainTimer(
            stepId = "step_1",
            state = "running",
            durationS = 60,
            remainingS = 30,
            anchorElapsedMs = 100L,
            savedAtEpochMs = 1_000L,
            updatedAt = "2026-11-05T00:00:00Z",
        )
        val gateway = FakeGateway(
            initialProgress = DomainProgress(
                currentStepId = "step_1",
                stepStatuses = mapOf("step_1" to "in_progress"),
                evidenceLevels = mapOf("step_1" to "none"),
                timer = invalidTimer,
            ),
        )
        val viewModel = StepViewModel(
            gateway,
            FakeCache(),
            TimerEngine { testScheduler.currentTime },
            { testScheduler.currentTime },
        )
        runCurrent()
        assertTrue(viewModel.state.value.timerNeedsConfirmation)

        viewModel.confirmTimerReset()
        runCurrent()
        assertEquals("running", viewModel.state.value.timer?.state)
        advanceTimeBy(5_000)
        runCurrent()
        assertTrue(viewModel.state.value.timerRemainingS < 60)

        viewModel.pauseTimer()
        runCurrent()
        advanceTimeBy(1_000)
        runCurrent()
    }

    @Test
    fun resetWhileFinishedPatchPendingKeepsNewCountdown() = runTest(dispatcher) {
        val gateway = FakeGateway()
        gateway.blockFinishedPatch = true
        val viewModel = StepViewModel(
            gateway,
            FakeCache(),
            TimerEngine { testScheduler.currentTime },
            { testScheduler.currentTime },
        )
        runCurrent()

        viewModel.startTimer()
        runCurrent()
        advanceTimeBy(60_000)
        runCurrent()
        assertEquals("finished", viewModel.state.value.timer?.state)
        val oldPatch = gateway.finishedPatchGate
        assertTrue(oldPatch != null)

        viewModel.resetTimer()
        runCurrent()
        assertEquals("running", viewModel.state.value.timer?.state)
        assertEquals(60, viewModel.state.value.timerRemainingS)

        advanceTimeBy(5_000)
        runCurrent()
        val remainingAfterReset = viewModel.state.value.timerRemainingS
        assertTrue(remainingAfterReset < 60)

        oldPatch!!.complete(Unit)
        runCurrent()
        assertEquals("running", viewModel.state.value.timer?.state)
        assertEquals(remainingAfterReset, viewModel.state.value.timerRemainingS)

        advanceTimeBy(2_000)
        runCurrent()
        assertTrue(viewModel.state.value.timerRemainingS < remainingAfterReset)

        viewModel.pauseTimer()
        runCurrent()
        advanceTimeBy(1_000)
        runCurrent()
    }

    @Test
    fun completeStepPatchFailureShowsErrorAndKeepsCounting() = runTest(dispatcher) {
        val gateway = FakeGateway()
        val viewModel = StepViewModel(
            gateway,
            FakeCache(),
            TimerEngine { testScheduler.currentTime },
            { testScheduler.currentTime },
        )
        runCurrent()

        viewModel.startTimer()
        runCurrent()
        advanceTimeBy(2_000)
        runCurrent()
        val remainingBeforeFailure = viewModel.state.value.timerRemainingS
        assertTrue(remainingBeforeFailure < 60)

        gateway.failUpdates = true
        viewModel.completeStep()
        runCurrent()

        assertTrue(viewModel.state.value.error != null)
        assertEquals(0, viewModel.state.value.index)
        assertEquals("running", viewModel.state.value.timer?.state)

        advanceTimeBy(2_000)
        runCurrent()
        assertTrue(viewModel.state.value.timerRemainingS < remainingBeforeFailure)

        gateway.failUpdates = false
        viewModel.pauseTimer()
        runCurrent()
        advanceTimeBy(1_000)
        runCurrent()
    }

    @Test
    fun resetTimerPatchFailureKeepsOldRunningTimerCounting() = runTest(dispatcher) {
        val gateway = FakeGateway()
        val viewModel = StepViewModel(
            gateway,
            FakeCache(),
            TimerEngine { testScheduler.currentTime },
            { testScheduler.currentTime },
        )
        runCurrent()

        viewModel.startTimer()
        runCurrent()
        advanceTimeBy(2_000)
        runCurrent()
        val remainingBeforeFailure = viewModel.state.value.timerRemainingS

        gateway.failUpdates = true
        viewModel.resetTimer()
        runCurrent()

        assertTrue(viewModel.state.value.error != null)
        assertEquals("running", viewModel.state.value.timer?.state)
        assertTrue(viewModel.state.value.timerRemainingS <= remainingBeforeFailure)

        advanceTimeBy(2_000)
        runCurrent()
        assertTrue(viewModel.state.value.timerRemainingS < remainingBeforeFailure)

        gateway.failUpdates = false
        viewModel.pauseTimer()
        runCurrent()
        advanceTimeBy(1_000)
        runCurrent()
    }

    @Test
    fun staleTimerFailureDoesNotAffectNewerTimerOperation() = runTest(dispatcher) {
        val gateway = FakeGateway()
        val viewModel = StepViewModel(
            gateway,
            FakeCache(),
            TimerEngine { testScheduler.currentTime },
            { testScheduler.currentTime },
        )
        runCurrent()

        viewModel.startTimer()
        runCurrent()
        advanceTimeBy(1_000)
        runCurrent()

        gateway.failUpdates = true
        gateway.blockFailingPatch = true
        viewModel.resetTimer()
        runCurrent()
        val oldFailure = gateway.failingPatchGate
        assertTrue(oldFailure != null)

        gateway.failUpdates = false
        viewModel.resetTimer()
        runCurrent()
        assertEquals("running", viewModel.state.value.timer?.state)
        assertEquals(60, viewModel.state.value.timerRemainingS)
        assertTrue(viewModel.state.value.error == null)

        oldFailure!!.complete(Unit)
        runCurrent()
        assertTrue(viewModel.state.value.error == null)
        assertEquals("running", viewModel.state.value.timer?.state)
        assertEquals(60, viewModel.state.value.timerRemainingS)

        advanceTimeBy(2_000)
        runCurrent()
        assertTrue(viewModel.state.value.timerRemainingS < 60)

        viewModel.pauseTimer()
        runCurrent()
        advanceTimeBy(1_000)
        runCurrent()
    }
}