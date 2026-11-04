package com.tutorialcoach.app.ui.screens.clarify

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
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
import androidx.compose.runtime.mutableStateMapOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import com.tutorialcoach.app.di.AppContainer
import com.tutorialcoach.app.domain.DomainQuestion
import com.tutorialcoach.app.ui.components.ErrorBanner

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ClarifyScreen(
    container: AppContainer,
    onReady: () -> Unit,
    onBack: () -> Unit,
) {
    val viewModel: ClarifyViewModel = viewModel(
        factory = viewModelFactory {
            initializer { ClarifyViewModel(container.repository) }
        },
    )
    val session by viewModel.session.collectAsStateWithLifecycle()
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    val values = remember { mutableStateMapOf<String, String>() }
    val questionKey = session?.questions?.joinToString("|") { it.id }.orEmpty()

    LaunchedEffect(session?.id, questionKey) {
        values.clear()
    }
    LaunchedEffect(Unit) {
        viewModel.events.collect { onReady() }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("澄清条件") },
                navigationIcon = {
                    TextButton(onClick = onBack) { Text("返回") }
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
            val current = session
            if (current == null) {
                Text("会话未加载，请返回首页重新创建。")
                return@Column
            }
            Text(current.goal, style = MaterialTheme.typography.titleMedium)
            Text(
                text = "最多两轮澄清；可回答非必填问题，也可留空跳过。",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )

            if (current.status == "ready") {
                Text("条件已足够，可以生成计划。")
                Button(
                    onClick = onReady,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(52.dp),
                ) {
                    Text("去生成计划")
                }
                return@Column
            }

            if (current.questions.isEmpty()) {
                Text("当前没有待回答问题。")
                return@Column
            }

            current.questions.forEach { question ->
                QuestionCard(
                    question = question,
                    value = values[question.id].orEmpty(),
                    onValueChange = { values[question.id] = it },
                )
            }

            if (uiState is ClarifyUiState.Error) {
                val error = uiState as ClarifyUiState.Error
                ErrorBanner(
                    message = error.message,
                    retryable = error.retryable,
                    onRetry = { viewModel.submit(values.toMap()) },
                    onDismiss = viewModel::dismissError,
                )
            }

            Button(
                onClick = { viewModel.submit(values.toMap()) },
                enabled = uiState !is ClarifyUiState.Loading,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(52.dp),
            ) {
                Text(if (uiState is ClarifyUiState.Loading) "提交中…" else "提交回答")
            }
        }
    }
}

@Composable
private fun QuestionCard(
    question: DomainQuestion,
    value: String,
    onValueChange: (String) -> Unit,
) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text(
                text = if (question.required) "${question.prompt} *" else question.prompt,
                style = MaterialTheme.typography.titleSmall,
            )
            if (question.help.isNotBlank()) {
                Text(
                    text = question.help,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            when (question.kind) {
                "single_choice" -> Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                    question.options.forEach { option ->
                        FilterChip(
                            selected = value == option,
                            onClick = { onValueChange(option) },
                            label = { Text(optionLabel(option)) },
                            modifier = Modifier.height(48.dp),
                        )
                    }
                }
                "boolean" -> Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    FilterChip(
                        selected = value == "true",
                        onClick = { onValueChange("true") },
                        label = { Text("是") },
                        modifier = Modifier.height(48.dp),
                    )
                    FilterChip(
                        selected = value == "false",
                        onClick = { onValueChange("false") },
                        label = { Text("否") },
                        modifier = Modifier.height(48.dp),
                    )
                }
                "number" -> OutlinedTextField(
                    value = value,
                    onValueChange = onValueChange,
                    label = { Text(question.unit ?: "数字") },
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                )
                "multi_choice" -> OutlinedTextField(
                    value = value,
                    onValueChange = onValueChange,
                    label = { Text("多个选项用英文逗号分隔") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                )
                else -> OutlinedTextField(
                    value = value,
                    onValueChange = onValueChange,
                    label = { Text("回答") },
                    modifier = Modifier.fillMaxWidth(),
                )
            }
        }
    }
}

private fun optionLabel(value: String): String = when (value) {
    "beginner" -> "初学者"
    "intermediate" -> "有一定经验"
    "advanced" -> "熟练"
    "gas" -> "燃气灶"
    "induction" -> "电磁炉"
    "electric" -> "电热灶"
    "none" -> "没有灶具"
    "natural" -> "自然光"
    "indoor" -> "室内灯光"
    "studio" -> "影棚灯"
    "mixed" -> "混合光"
    "low_light" -> "低光"
    "none_stabilization" -> "无稳定"
    "handheld" -> "手持"
    "gimbal" -> "稳定器"
    "tripod" -> "三脚架"
    "slider" -> "滑轨"
    "windows" -> "Windows"
    "macos" -> "macOS"
    "linux" -> "Linux"
    "android" -> "Android"
    "ios" -> "iOS"
    else -> value
}