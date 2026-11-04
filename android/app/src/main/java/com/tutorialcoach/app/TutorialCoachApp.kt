package com.tutorialcoach.app

import android.app.Application
import com.tutorialcoach.app.di.AppContainer

class TutorialCoachApp : Application() {
    lateinit var container: AppContainer
        private set

    override fun onCreate() {
        super.onCreate()
        container = AppContainer()
    }
}