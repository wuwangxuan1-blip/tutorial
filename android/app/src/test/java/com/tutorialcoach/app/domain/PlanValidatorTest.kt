package com.tutorialcoach.app.domain

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class PlanValidatorTest {
    private fun step(order: Int, criteria: List<String> = listOf("可观察标准")) = DomainStep(
        id = "step_$order",
        order = order,
        phase = "execute",
        title = "步骤 $order",
        instruction = "执行步骤 $order。",
        why = "原因",
        durationS = 60,
        completionCriteria = criteria,
        safety = emptyList(),
        commonMistakes = emptyList(),
        evidenceHint = "",
        mediaPrompt = "",
    )

    private fun plan(steps: List<DomainStep>) = DomainPlan(
        id = "plan_1",
        sessionId = "sess_1",
        version = 1,
        domain = "cooking",
        title = "测试计划",
        summary = "",
        assumptions = emptyList(),
        preparation = emptyList(),
        steps = steps,
        totalEstimatedMin = 30,
        safetyNotes = emptyList(),
    )

    @Test
    fun validPlanHasNoErrors() {
        val errors = PlanValidator.validate(plan(listOf(step(1), step(2), step(3))))
        assertTrue(errors.isEmpty())
    }

    @Test
    fun missingCompletionCriteriaIsRejected() {
        val errors = PlanValidator.validate(plan(listOf(step(1), step(2), step(3, emptyList()))))
        assertEquals(1, errors.count { it.contains("完成标准") })
    }

    @Test
    fun tooFewStepsIsRejected() {
        val errors = PlanValidator.validate(plan(listOf(step(1), step(2))))
        assertTrue(errors.any { it.contains("3–15") })
    }

    @Test
    fun brokenOrderIsRejected() {
        val errors = PlanValidator.validate(plan(listOf(step(1), step(3), step(2))))
        assertTrue(errors.any { it.contains("顺序不连续") })
    }
}