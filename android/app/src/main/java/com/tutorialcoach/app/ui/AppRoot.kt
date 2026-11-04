package com.tutorialcoach.app.ui

import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import com.tutorialcoach.app.di.AppContainer
import com.tutorialcoach.app.ui.screens.clarify.ClarifyScreen
import com.tutorialcoach.app.ui.screens.home.HomeScreen
import com.tutorialcoach.app.ui.screens.plan.PlanScreen
import com.tutorialcoach.app.ui.screens.settings.DiagnosticsScreen
import com.tutorialcoach.app.ui.screens.step.StepScreen

private const val SCREEN_HOME = "home"
private const val SCREEN_CLARIFY = "clarify"
private const val SCREEN_PLAN = "plan"
private const val SCREEN_STEP = "step"
private const val SCREEN_DIAGNOSTICS = "diagnostics"

@Composable
fun AppRoot(container: AppContainer) {
    var screen by rememberSaveable { mutableStateOf(SCREEN_HOME) }

    when (screen) {
        SCREEN_HOME -> HomeScreen(
            container = container,
            onCreated = { status ->
                screen = if (status == "ready") SCREEN_PLAN else SCREEN_CLARIFY
            },
            onDiagnostics = { screen = SCREEN_DIAGNOSTICS },
        )
        SCREEN_CLARIFY -> ClarifyScreen(
            container = container,
            onReady = { screen = SCREEN_PLAN },
            onBack = { screen = SCREEN_HOME },
        )
        SCREEN_PLAN -> PlanScreen(
            container = container,
            onOpenStep = { screen = SCREEN_STEP },
            onBack = { screen = SCREEN_HOME },
        )
        SCREEN_STEP -> StepScreen(
            container = container,
            onBack = { screen = SCREEN_PLAN },
        )
        SCREEN_DIAGNOSTICS -> DiagnosticsScreen(
            container = container,
            onBack = { screen = SCREEN_HOME },
        )
    }
}