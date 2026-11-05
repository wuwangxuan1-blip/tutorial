package com.tutorialcoach.app.di

import com.tutorialcoach.app.data.ApiClient
import com.tutorialcoach.app.data.RateLimitGate
import com.tutorialcoach.app.data.SessionRepository

class AppContainer(
    baseUrl: String = DEFAULT_BASE_URL,
) {
    val apiClient: ApiClient = ApiClient(baseUrl)
    val repository: SessionRepository = SessionRepository(apiClient)
    val rateLimitGate: RateLimitGate = RateLimitGate()

    companion object {
        const val DEFAULT_BASE_URL = "http://127.0.0.1:8000"
    }
}