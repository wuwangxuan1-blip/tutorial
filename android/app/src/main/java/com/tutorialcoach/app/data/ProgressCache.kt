package com.tutorialcoach.app.data

import com.tutorialcoach.app.domain.DomainProgress
import com.tutorialcoach.app.domain.DomainTimer

interface ProgressCache {
    fun saveProgress(progress: DomainProgress)

    fun currentStepId(): String?

    fun loadTimer(): DomainTimer?
}