package com.tutorialcoach.app.ui.screens.settings

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Card
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import com.tutorialcoach.app.di.AppContainer
import com.tutorialcoach.app.ui.components.ErrorBanner

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DiagnosticsScreen(
    container: AppContainer,
    onBack: () -> Unit,
) {
    val viewModel: DiagnosticsViewModel = viewModel(
        factory = viewModelFactory {
            initializer { DiagnosticsViewModel(container.repository) }
        },
    )
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("诊断") },
                navigationIcon = {
                    TextButton(onClick = onBack) { Text("返回") }
                },
                actions = {
                    TextButton(onClick = viewModel::refresh) { Text("刷新") }
                },
            )
        },
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            InfoCard(title = "连接地址") {
                Text(AppContainer.DEFAULT_BASE_URL, style = MaterialTheme.typography.bodyMedium)
                Text(
                    "真机联调：adb reverse tcp:8000 tcp:8000",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                Text(
                    "Key 只在服务端 .env；APK 不读取、不保存 Key。",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }

            when (val state = uiState) {
                is DiagnosticsUiState.Loading -> {
                    InfoCard(title = "服务端健康") {
                        Text("检查中…")
                    }
                }
                is DiagnosticsUiState.Error -> {
                    ErrorBanner(
                        message = state.message,
                        retryable = true,
                        onRetry = viewModel::refresh,
                    )
                }
                is DiagnosticsUiState.Ready -> {
                    InfoCard(title = "服务端健康") {
                        InfoRow("status", state.health.status)
                        InfoRow("api_version", state.health.apiVersion)
                        InfoRow("store", state.health.checks.store.toString())
                        InfoRow("ffmpeg", state.health.checks.ffmpeg.toString())
                        InfoRow("model_configured", state.health.checks.modelConfigured.toString())
                    }
                    InfoCard(title = "模型能力") {
                        InfoRow("text_model", state.capabilities.model.textModel ?: "未配置")
                        InfoRow("vision_model", state.capabilities.model.visionModel ?: "未配置")
                        InfoRow("configured", state.capabilities.model.configured.toString())
                        InfoRow(
                            "vision_supported",
                            when (state.capabilities.model.visionSupported) {
                                true -> "探针通过"
                                false -> "探针不支持"
                                null -> "未探测"
                            },
                        )
                        InfoRow("probe_at", state.capabilities.model.probeAt ?: "无")
                        InfoRow("audio_analysis", state.capabilities.model.audioAnalysis.toString())
                    }
                    InfoCard(title = "领域") {
                        Text(
                            state.capabilities.domains.joinToString(" · "),
                            style = MaterialTheme.typography.bodyMedium,
                        )
                        Text(
                            "P0 只开放烹饪计划生成。",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun InfoCard(title: String, content: @Composable () -> Unit) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            Text(title, style = MaterialTheme.typography.titleSmall)
            content()
        }
    }
}

@Composable
private fun InfoRow(label: String, value: String) {
    Row(
        horizontalArrangement = Arrangement.spacedBy(8.dp),
        modifier = Modifier.fillMaxWidth(),
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
        Text(text = value, style = MaterialTheme.typography.bodySmall)
    }
}