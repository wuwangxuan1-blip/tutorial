package com.tutorialcoach.app.ui.screens.plan

import com.tutorialcoach.app.data.JobDto
import com.tutorialcoach.app.data.JobResultDto
import com.tutorialcoach.app.data.NetworkException
import com.tutorialcoach.app.data.PlanGateway
import com.tutorialcoach.app.domain.DomainPlan
import com.tutorialcoach.app.domain.DomainSession
import com.tutorialcoach.app.domain.DomainStep
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
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class PlanViewModelTest {
    private val dispatcher = StandardTestDispatcher()

    @Before
    fun setUp() {
        Dispatchers.setMain(dispatcher)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    private fun makeSession(id: String = "sess_1") = DomainSession(
        id = id,
        domain = "cooking",
        goal = "2 人份番茄鸡蛋面",
        status = "ready",
        questions = emptyList(),
        currentPlanVersion = null,
    )

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

    private inner class FakeGateway : PlanGateway {
        private val _session = MutableStateFlow<DomainSession?>(makeSession())
        override val session: StateFlow<DomainSession?> = _session

        private val _plan = MutableStateFlow<DomainPlan?>(null)
        override val plan: StateFlow<DomainPlan?> = _plan

        var createCalls = 0
        var loadCalls = 0
        var failFirstLoad = true

        override suspend fun createPlanJob(
            sessionId: String,
            basePlanVersion: Int?,
            idempotencyKey: String,
        ): JobDto {
            createCalls += 1
            return JobDto(
                id = "job_1",
                type = "plan_generation",
                status = "succeeded",
                progress = 100,
                stage = "succeeded",
                sessionId = sessionId,
                result = JobResultDto(planId = "plan_1", planVersion = 1),
            )
        }

        override suspend fun getJob(jobId: String): JobDto = JobDto(
            id = jobId,
            type = "plan_generation",
            status = "succeeded",
            progress = 100,
            stage = "succeeded",
            sessionId = _session.value?.id ?: "sess_1",
            result = JobResultDto(planId = "plan_1", planVersion = 1),
        )

        override suspend fun loadPlan(sessionId: String): DomainPlan {
            loadCalls += 1
            if (failFirstLoad && loadCalls == 1) {
                throw NetworkException("offline")
            }
            val value = makePlan()
            _plan.value = value
            _session.value = _session.value?.copy(currentPlanVersion = 1)
            return value
        }
    }

    @Test
    fun successfulJobWithFailedPlanFetchRetriesOnlyTheFetch() = runTest(dispatcher) {
        val gateway = FakeGateway()
        val viewModel = PlanViewModel(gateway)
        advanceUntilIdle()

        viewModel.generate()
        advanceUntilIdle()
        assertTrue(viewModel.uiState.value is PlanUiState.Error)
        assertTrue((viewModel.uiState.value as PlanUiState.Error).message.contains("获取计划失败"))
        assertEquals(1, gateway.createCalls)
        assertEquals(1, gateway.loadCalls)

        viewModel.retry()
        advanceUntilIdle()
        assertTrue(viewModel.uiState.value is PlanUiState.Ready)
        assertEquals(1, gateway.createCalls)
        assertEquals(2, gateway.loadCalls)
        assertEquals(1, gateway.session.value?.currentPlanVersion ?: -1)
    }
}