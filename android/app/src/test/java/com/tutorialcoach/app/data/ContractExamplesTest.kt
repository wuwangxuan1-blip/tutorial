package com.tutorialcoach.app.data

import kotlinx.serialization.builtins.ListSerializer
import kotlinx.serialization.json.Json
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class ContractExamplesTest {
    private val json = Json {
        ignoreUnknownKeys = true
        explicitNulls = false
    }

    private fun read(name: String): String {
        val stream = requireNotNull(javaClass.getResourceAsStream("/$name")) {
            "missing contract example resource: $name"
        }
        return stream.bufferedReader(Charsets.UTF_8).use { it.readText() }
    }

    @Test
    fun createSessionRequestExampleParses() {
        val request = json.decodeFromString(
            CreateSessionRequest.serializer(),
            read("session_create_request.json"),
        )
        assertEquals("cooking", request.domain)
        assertEquals("2 人份番茄鸡蛋面，30 分钟内完成", request.goal)
        assertTrue(request.referenceIds.isEmpty())
        assertEquals("beginner", request.conditions["skill_level"].toString().trim('"'))
        assertEquals("30", request.conditions["time_budget_min"].toString())
        assertEquals("2", request.conditions["people"].toString())
    }

    @Test
    fun questionsExampleParsesWithEnumsAndNullability() {
        val questions = json.decodeFromString(
            ListSerializer(QuestionDto.serializer()),
            read("questions.json"),
        )
        assertEquals(5, questions.size)
        assertEquals(
            listOf("servings", "stove_type", "oven_available", "allergies", "available_equipment"),
            questions.map { it.field },
        )
        assertTrue(questions.all { it.id.startsWith("q_") })
        assertEquals("single_choice", questions[1].kind)
        assertEquals(listOf("gas", "induction", "electric", "none"), questions[1].options)
        assertEquals("份", questions[0].unit)
        assertNull(questions[2].unit)

        val decoded = json.decodeFromString(
            ListSerializer(QuestionDto.serializer()),
            json.encodeToString(ListSerializer(QuestionDto.serializer()), questions),
        )
        assertEquals(questions, decoded)
    }

    @Test
    fun sessionExampleParsesAndRoundTrips() {
        val session = json.decodeFromString(SessionDto.serializer(), read("session.json"))
        assertEquals("cooking", session.domain)
        assertEquals("clarifying", session.status)
        assertNull(session.currentPlanVersion)
        assertNull(session.progress.timer)
        assertTrue(session.progress.evidenceLevels.isEmpty())
        assertEquals(5, session.questions.size)
        assertEquals("beginner", session.conditions["skill_level"].toString().trim('"'))

        val roundTrip = json.decodeFromString(
            SessionDto.serializer(),
            json.encodeToString(SessionDto.serializer(), session),
        )
        assertEquals(session, roundTrip)
    }

    @Test
    fun planExampleParsesAndHasObservableSteps() {
        val plan = json.decodeFromString(PlanDto.serializer(), read("plan_cooking.json"))
        assertEquals("cooking", plan.domain)
        assertEquals(1, plan.version)
        assertTrue(plan.steps.size in 3..15)
        assertEquals(listOf(1, 2, 3), plan.steps.map { it.order })
        assertTrue(plan.steps.all { it.completionCriteria.isNotEmpty() })
        assertTrue(plan.steps.all { it.id.startsWith("step_") })
        assertTrue(plan.preparation.all { it.id.startsWith("prep_") })
        assertNull(plan.steps[0].visualAid)
        assertNotNull(plan.steps[0].timer)
        assertTrue(plan.steps.all { it.phase in setOf("prepare", "execute", "verify", "finish") })

        val roundTrip = json.decodeFromString(
            PlanDto.serializer(),
            json.encodeToString(PlanDto.serializer(), plan),
        )
        assertEquals(plan, roundTrip)
    }

    @Test
    fun jobSuccessAndFailureExamplesParse() {
        val success = json.decodeFromString(JobDto.serializer(), read("job.json"))
        assertEquals("plan_generation", success.type)
        assertEquals("succeeded", success.status)
        assertEquals("done", success.stage)
        assertEquals("plan_01J9Z8M1AA", success.result?.planId)
        assertEquals(1, success.result?.planVersion)
        assertNull(success.error)

        val failure = json.decodeFromString(JobDto.serializer(), read("job_failed.json"))
        assertEquals("failed", failure.status)
        assertNull(failure.result)
        assertEquals("MODEL_TIMEOUT", failure.error?.error?.code)
        assertEquals(true, failure.error?.error?.retryable)
        assertEquals(5, failure.error?.error?.retryAfterS)
    }

    @Test
    fun errorExampleParsesEnvelopeFormat() {
        val envelope = json.decodeFromString(ErrorEnvelopeDto.serializer(), read("error_version_conflict.json"))
        assertEquals("VERSION_CONFLICT", envelope.error.code)
        assertEquals(false, envelope.error.retryable)
        assertNull(envelope.error.retryAfterS)
        assertEquals("req_01J9Z9K1AA", envelope.error.requestId)
        assertEquals("2", envelope.error.details["current_plan_version"]?.toString())
    }
}