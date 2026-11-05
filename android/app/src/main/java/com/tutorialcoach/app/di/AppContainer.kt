package com.tutorialcoach.app.di

import android.content.Context
import com.tutorialcoach.app.data.ApiClient
import com.tutorialcoach.app.data.LocalStore
import com.tutorialcoach.app.data.RateLimitGate
import com.tutorialcoach.app.data.SessionRepository

class AppContainer(
    context: Context,
    baseUrl: String = DEFAULT_BASE_URL,
) {
    val apiClient: ApiClient = ApiClient(baseUrl)
    val localStore: LocalStore = LocalStore(context)
    val repository: SessionRepository = SessionRepository(apiClient, localStore)
    val rateLimitGate: RateLimitGate = RateLimitGate()

    companion object {
        const val DEFAULT_BASE_URL = "http://127.0.0.1:8000"
    }
}