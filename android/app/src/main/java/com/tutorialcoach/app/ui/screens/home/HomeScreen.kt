package com.tutorialcoach.app.ui.screens.home

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import com.tutorialcoach.app.di.AppContainer
import com.tutorialcoach.app.ui.components.ErrorBanner

private data class DomainOption(val value: String, val label: String)

private val domains = listOf(
    DomainOption("cooking", "烹饪与烘焙"),
    DomainOption("photography", "摄影与视频"),
    DomainOption("software", "软件与数字技能"),
    DomainOption("coffee", "咖啡与饮品"),
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    container: AppContainer,
    onCreated: (String) -> Unit,
    onDiagnostics: () -> Unit,
) {
    val viewModel: HomeViewModel = viewModel(
        factory = viewModelFactory {
            initializer { HomeViewModel(container.repository) }
        },
    )
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    val serviceStatus by viewModel.serviceStatus.collectAsStateWithLifecycle()
    var goal by remember { mutableStateOf("") }
    var domain by remember { mutableStateOf("cooking") }

    LaunchedEffect(Unit) {
        viewModel.events.collect { event ->
            when (event) {
                is HomeEvent.Created -> onCreated(event.status)
            }
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("实践陪练") },
                actions = {
                    TextButton(onClick = onDiagnostics) { Text("诊断") }
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
            Text(
                text = "输入一个实践目标，按领域补全条件，生成可执行的分步骤计划。",
                style = MaterialTheme.typography.bodyLarge,
            )
            Text(
                text = serviceStatusLabel(serviceStatus),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            TextButton(onClick = viewModel::refreshHealth) {
                Text("刷新服务端状态")
            }

            OutlinedTextField(
                value = goal,
                onValueChange = { if (it.length <= 500) goal = it },
                label = { Text("实践目标") },
                placeholder = { Text("例如：2 人份番茄鸡蛋面，30 分钟内完成") },
                supportingText = { Text("${goal.length}/500") },
                minLines = 3,
                modifier = Modifier.fillMaxWidth(),
            )

            Text("领域", style = MaterialTheme.typography.titleMedium)
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    DomainChip(domains[0], domain) { domain = it }
                    DomainChip(domains[1], domain) { domain = it }
                }
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    DomainChip(domains[2], domain) { domain = it }
                    DomainChip(domains[3], domain) { domain = it }
                }
            }

            Text(
                text = "当前阶段（P2/D3）开放烹饪与软件领域的真实模型计划；其它领域可创建会话和澄清，计划生成在后续阶段开放。",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )

            if (uiState is HomeUiState.Error) {
                val error = uiState as HomeUiState.Error
                ErrorBanner(
                    message = error.message,
                    retryable = error.retryable,
                    onRetry = { viewModel.create(goal, domain) },
                    onDismiss = viewModel::dismissError,
                )
            }

            Button(
                onClick = { viewModel.create(goal, domain) },
                enabled = uiState !is HomeUiState.Loading,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(52.dp),
            ) {
                if (uiState is HomeUiState.Loading) {
                    CircularProgressIndicator(
                        modifier = Modifier.height(20.dp),
                        strokeWidth = 2.dp,
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("创建中…")
                } else {
                    Text("创建会话")
                }
            }

            Text(
                text = "提示：真实模型调用可能需要 30–90 秒；无 Key、超时或格式错误时会显示明确错误，不展示假计划。",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun DomainChip(
    option: DomainOption,
    selectedValue: String,
    onSelect: (String) -> Unit,
) {
    FilterChip(
        selected = selectedValue == option.value,
        onClick = { onSelect(option.value) },
        label = { Text(option.label) },
        modifier = Modifier.height(48.dp),
    )
}

private fun serviceStatusLabel(status: String?): String = when (status) {
    "ok" -> "服务端：正常"
    "degraded" -> "服务端：降级（可能未配置模型 Key）"
    "offline" -> "服务端：未连接"
    null -> "服务端：检查中…"
    else -> "服务端：$status"
}