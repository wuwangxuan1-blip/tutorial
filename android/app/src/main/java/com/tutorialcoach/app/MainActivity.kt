package com.tutorialcoach.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import com.tutorialcoach.app.ui.AppRoot
import com.tutorialcoach.app.ui.theme.TutorialCoachTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val container = (application as TutorialCoachApp).container
        setContent {
            TutorialCoachTheme {
                AppRoot(container)
            }
        }
    }
}