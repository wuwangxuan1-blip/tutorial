package com.tutorialcoach.app.data

data class ProgressUpdate(
    val basePlanVersion: Int,
    val currentStepId: String? = null,
    val includeCurrentStep: Boolean = false,
    val stepStatuses: Map<String, String>? = null,
    val evidenceLevels: Map<String, String>? = null,
    val timer: TimerDto? = null,
    val includeTimer: Boolean = false,
)