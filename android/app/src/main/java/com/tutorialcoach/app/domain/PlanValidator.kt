package com.tutorialcoach.app.domain

object PlanValidator {
    private val phases = setOf("prepare", "execute", "verify", "finish")

    fun validate(plan: DomainPlan): List<String> {
        val errors = mutableListOf<String>()
        if (plan.title.isBlank()) {
            errors += "计划标题为空。"
        }
        if (plan.steps.size !in 3..15) {
            errors += "计划步骤数量必须在 3–15 个。"
        }
        if (plan.totalEstimatedMin !in 5..480) {
            errors += "预计总时长必须在 5–480 分钟。"
        }
        plan.steps.forEachIndexed { index, step ->
            if (step.order != index + 1) {
                errors += "步骤顺序不连续。"
            }
            if (step.title.isBlank() || step.instruction.isBlank()) {
                errors += "第 ${index + 1} 步缺少标题或说明。"
            }
            if (step.phase !in phases) {
                errors += "第 ${index + 1} 步阶段无效。"
            }
            if (step.durationS !in 0..7200) {
                errors += "第 ${index + 1} 步时长无效。"
            }
            if (step.completionCriteria.isEmpty()) {
                errors += "第 ${index + 1} 步缺少可观察完成标准。"
            }
        }
        return errors.distinct()
    }
}