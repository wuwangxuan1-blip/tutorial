package com.tutorialcoach.app.data

import com.tutorialcoach.app.domain.CameraMoveValidator
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
    fun cameraMoveVisualAidParsesAndValidates() {
        val payload = """
            {
              "id": "plan_cam",
              "session_id": "sess_cam",
              "version": 1,
              "domain": "photography",
              "title": "环绕拍咖啡",
              "summary": "",
              "assumptions": [],
              "preparation": [{"id": "prep_1", "text": "摆好咖啡杯", "optional": false}],
              "steps": [
                {
                  "id": "step_1",
                  "order": 1,
                  "phase": "execute",
                  "title": "环绕",
                  "instruction": "绕杯一周。",
                  "duration_s": 8,
                  "completion_criteria": ["主体在画面内"],
                  "visual_aid": {
                    "type": "camera_move",
                    "camera_move": {
                      "id": "cam_1",
                      "shot_type": "orbit_cw",
                      "motion_type": "camera_move",
                      "technique": "handheld",
                      "subject_anchor": {"x": 0.5, "y": 0.5, "label": "咖啡杯"},
                      "position_path": {
                        "space": "normalized_top_down",
                        "start": {"x": 0.3, "y": 0.7},
                        "end": {"x": 0.7, "y": 0.3},
                        "control": null,
                        "arc": "cw"
                      },
                      "orientation_path": null,
                      "zoom": null,
                      "duration_s": 8,
                      "easing": "ease_in_out",
                      "aspect_ratio": "9:16",
                      "notes": [],
                      "limitations": ["2D 俯视示意，不代表真实焦距。"]
                    }
                  }
                }
              ],
              "total_estimated_min": 15,
              "safety_notes": [],
              "reference_ids": [],
              "created_at": "2026-11-05T00:00:00Z"
            }
        """.trimIndent()

        val plan = json.decodeFromString(PlanDto.serializer(), payload).toDomain()
        val camera = plan.steps.first().cameraMove
        assertEquals("camera_move", plan.steps.first().visualAidType)
        assertEquals("orbit_cw", camera?.shotType)
        assertTrue(CameraMoveValidator.validate(camera!!).isEmpty())
    }

    @Test
    fun recipeDtoParsesVariablesAndSteps() {
        val payload = """
            {
              "id": "recipe_01",
              "session_id": "sess_01",
              "version": 1,
              "name": "V60 手冲",
              "brewer": "V60",
              "method": "pour_over",
              "servings": 1,
              "variables": {"dose_g": 15, "water_g": 225, "ratio": 15.0, "water_temp_c": 92, "grind_setting": "中细", "brew_time_s": 150},
              "ingredients": [{"name": "咖啡豆", "amount": 15, "unit": "g"}],
              "steps": [{"id": "rst_1", "order": 1, "instruction": "闷蒸 30 秒", "duration_s": 30, "target": "粉层湿润"}],
              "source_plan_version": 1,
              "created_at": "2026-11-05T00:00:00Z"
            }
        """.trimIndent()

        val recipe = json.decodeFromString(RecipeDto.serializer(), payload).toDomain()
        assertEquals(15.0, recipe.variables.doseG!!, 0.001)
        assertEquals(225.0, recipe.variables.waterG!!, 0.001)
        assertEquals(92.0, recipe.variables.waterTempC!!, 0.001)
        assertEquals("中细", recipe.variables.grindSetting)
        assertEquals(1, recipe.steps.size)
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