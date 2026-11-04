package com.tutorialcoach.app.data

import kotlinx.serialization.json.Json
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class DtoTest {
    private val json = Json {
        ignoreUnknownKeys = true
        explicitNulls = false
    }

    @Test
    fun sessionDtoParsesContractFieldsAndUnknownKeys() {
        val payload = """
            {
              "id": "sess_01J9Z8K6Q3",
              "domain": "cooking",
              "goal": "2 人份番茄鸡蛋面",
              "status": "clarifying",
              "conditions": {"time_budget_min": 30},
              "questions": [
                {
                  "id": "q_stove_type",
                  "field": "stove_type",
                  "prompt": "你使用什么灶具？",
                  "kind": "single_choice",
                  "required": true,
                  "options": ["gas", "induction", "electric", "none"],
                  "unit": null,
                  "help": "用于估算火力。",
                  "unexpected": "ignored"
                }
              ],
              "reference_ids": [],
              "current_plan_version": null,
              "progress": {
                "current_step_id": null,
                "step_statuses": {},
                "evidence_levels": {},
                "timer": null,
                "updated_at": "2026-11-04T08:00:00Z"
              },
              "outcome": null,
              "created_at": "2026-11-04T08:00:00Z",
              "updated_at": "2026-11-04T08:00:00Z"
            }
        """.trimIndent()

        val session = json.decodeFromString(SessionDto.serializer(), payload)
        assertEquals("sess_01J9Z8K6Q3", session.id)
        assertEquals(1, session.questions.size)
        assertTrue(session.questions.first().required)
        assertNull(session.currentPlanVersion)
        assertNull(session.questions.first().unit)
    }

    @Test
    fun planDtoParsesStepsAndTimers() {
        val payload = """
            {
              "id": "plan_01J9Z8M1AA",
              "session_id": "sess_01J9Z8K6Q3",
              "version": 1,
              "domain": "cooking",
              "title": "30 分钟番茄鸡蛋面",
              "summary": "先烧水，再炒蛋。",
              "assumptions": ["有炒锅"],
              "preparation": [{"id": "prep_1", "text": "切番茄", "optional": false}],
              "steps": [
                {
                  "id": "step_1",
                  "order": 1,
                  "phase": "prepare",
                  "title": "备料",
                  "instruction": "切番茄并打散鸡蛋。",
                  "why": "缩短时间。",
                  "duration_s": 300,
                  "completion_criteria": ["番茄切块"],
                  "safety": ["防烫"],
                  "common_mistakes": ["切得太大"],
                  "timer": {"suggested_s": 300, "auto_start": false},
                  "visual_aid": null,
                  "evidence_hint": "拍备料。",
                  "media_prompt": "需要检查吗？"
                }
              ],
              "total_estimated_min": 30,
              "safety_notes": ["生熟分开"],
              "reference_ids": [],
              "created_at": "2026-11-04T08:01:00Z"
            }
        """.trimIndent()

        val plan = json.decodeFromString(PlanDto.serializer(), payload)
        assertEquals(1, plan.steps.size)
        assertEquals("step_1", plan.steps.first().id)
        assertEquals(300, plan.steps.first().durationS)
        assertEquals(listOf("番茄切块"), plan.steps.first().completionCriteria)
    }

    @Test
    fun errorEnvelopeParsesRetryFields() {
        val payload = """
            {
              "error": {
                "code": "MODEL_RATE_LIMITED",
                "message": "模型限流，请稍后重试。",
                "retryable": true,
                "retry_after_s": 3,
                "request_id": "req_01J9Z9K1AA",
                "details": {}
              }
            }
        """.trimIndent()

        val envelope = json.decodeFromString(ErrorEnvelopeDto.serializer(), payload)
        assertEquals("MODEL_RATE_LIMITED", envelope.error.code)
        assertTrue(envelope.error.retryable)
        assertEquals(3, envelope.error.retryAfterS)
    }
}