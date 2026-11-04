package com.tutorialcoach.app.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val LightColors = lightColorScheme(
    primary = Color(0xFF1B6B4A),
    onPrimary = Color.White,
    primaryContainer = Color(0xFFB7F0D3),
    onPrimaryContainer = Color(0xFF002114),
    secondary = Color(0xFF4E6355),
    background = Color(0xFFF7FBF7),
    surface = Color(0xFFFFFFFF),
    error = Color(0xFFB3261E),
)

private val DarkColors = darkColorScheme(
    primary = Color(0xFF9CD6B8),
    onPrimary = Color(0xFF003824),
    primaryContainer = Color(0xFF005235),
    onPrimaryContainer = Color(0xFFB7F0D3),
    secondary = Color(0xFFB5CCBB),
    background = Color(0xFF101410),
    surface = Color(0xFF181D19),
)

@Composable
fun TutorialCoachTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit,
) {
    MaterialTheme(
        colorScheme = if (darkTheme) DarkColors else LightColors,
        content = content,
    )
}