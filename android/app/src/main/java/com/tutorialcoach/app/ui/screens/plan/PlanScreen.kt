package com.tutorialcoach.app.ui.screens.plan

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.LinearProgressIndicator
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
import com.tutorialcoach.app.domain.DomainPlan
import com.tutorialcoach.app.domain.DomainStep
import com.tutorialcoach.app.ui.components.ErrorBanner

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PlanScreen(
    container: AppContainer,
    onOpenStep: () -> Unit,
    onBack: () -> Unit,
) {
    val currentSession by container.repository.session.collectAsStateWithLifecycle()
    val viewModel: PlanViewModel = viewModel(
        key = currentSession?.id ?: "no-session",
        factory = viewModelFactory {
            initializer { PlanViewModel(container.repository, container.rateLimitGate) }
        },
    )
    val session by viewModel.session.collectAsStateWithLifecycle()
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
    val cooldownSeconds by viewModel.cooldownSeconds.collectAsStateWithLifecycle()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("计划") },
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
            session?.let {
                Text(it.goal, style = MaterialTheme.typography.titleMedium)
                Text(
                    text = "领域：${domainLabel(it.domain)}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }

            if (cooldownSeconds > 0) {
                Text(
                    text = "模型限流，请等待 $cooldownSeconds 秒后再试；等待期间不会创建新任务。",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.error,
                )
            }

            when (val state = uiState) {
                is PlanUiState.Working -> {
                    Text(
                        text = if (state.stage == "loading_plan") {
                            "计划已生成，正在获取计划…"
                        } else {
                            "正在调用真实模型生成计划（${stageLabel(state.stage)}）…"
                        },
                        style = MaterialTheme.typography.bodyLarge,
                    )
                    LinearProgressIndicator(modifier = Modifier.fillMaxWidth())
                    Text(
                        text = "进度约 ${state.progress}%。通常需要 30–90 秒，请保持服务端运行。",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
                is PlanUiState.Error -> {
                    ErrorBanner(
                        message = state.message,
                        retryable = state.retryable,
                        onRetry = if (cooldownSeconds == 0) viewModel::retry else null,
                        onDismiss = viewModel::dismissError,
                    )
                    GenerateButton(
                        onClick = viewModel::generate,
                        enabled = cooldownSeconds == 0,
                    )
                }
                is PlanUiState.Ready -> {
                    PlanContent(plan = state.plan, onOpenStep = onOpenStep)
                }
                PlanUiState.Idle -> {
                    Text("条件已就绪，点击下方按钮生成计划。")
                    GenerateButton(
                        onClick = viewModel::generate,
                        enabled = cooldownSeconds == 0,
                    )
                }
            }
        }
    }
}

@Composable
private fun GenerateButton(onClick: () -> Unit, enabled: Boolean = true) {
    Button(
        onClick = onClick,
        enabled = enabled,
        modifier = Modifier
            .fillMaxWidth()
            .height(52.dp),
    ) {
        Text("生成计划（真实模型）")
    }
}

@Composable
private fun PlanContent(plan: DomainPlan, onOpenStep: () -> Unit) {
    Text(plan.title, style = MaterialTheme.typography.headlineSmall)
    if (plan.summary.isNotBlank()) {
        Text(plan.summary, style = MaterialTheme.typography.bodyMedium)
    }
    Text(
        text = "预计 ${plan.totalEstimatedMin} 分钟 · 计划版本 v${plan.version} · ${plan.steps.size} 步",
        style = MaterialTheme.typography.bodySmall,
        color = MaterialTheme.colorScheme.onSurfaceVariant,
    )

    if (plan.assumptions.isNotEmpty()) {
        SectionCard(title = "假设") {
            plan.assumptions.forEach { Text("• $it", style = MaterialTheme.typography.bodyMedium) }
        }
    }

    if (plan.preparation.isNotEmpty()) {
        SectionCard(title = "准备清单") {
            plan.preparation.forEach {
                val suffix = if (it.optional) "（可选）" else ""
                Text("• ${it.text}$suffix", style = MaterialTheme.typography.bodyMedium)
            }
        }
    }

    if (plan.safetyNotes.isNotEmpty()) {
        SectionCard(title = "安全提示") {
            plan.safetyNotes.forEach { Text("• $it", style = MaterialTheme.typography.bodyMedium) }
        }
    }

    Text("步骤", style = MaterialTheme.typography.titleLarge)
    plan.steps.forEach { step ->
        StepSummaryCard(step)
    }

    Button(
        onClick = onOpenStep,
        modifier = Modifier
            .fillMaxWidth()
            .height(52.dp),
    ) {
        Text("打开步骤卡")
    }
}

@Composable
private fun SectionCard(title: String, content: @Composable () -> Unit) {
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
private fun StepSummaryCard(step: DomainStep) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(4.dp),
        ) {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("${step.order}.", style = MaterialTheme.typography.titleMedium)
                Text(step.title, style = MaterialTheme.typography.titleMedium)
            }
            Text(
                text = "${phaseLabel(step.phase)} · ${formatDuration(step.durationS)}",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Text(step.instruction, style = MaterialTheme.typography.bodyMedium)
        }
    }
}

private fun domainLabel(domain: String): String = when (domain) {
    "cooking" -> "烹饪与烘焙"
    "photography" -> "摄影与视频"
    "software" -> "软件与数字技能"
    "coffee" -> "咖啡与饮品"
    else -> domain
}

private fun phaseLabel(phase: String): String = when (phase) {
    "prepare" -> "准备"
    "execute" -> "执行"
    "verify" -> "验证"
    "finish" -> "收尾"
    else -> phase
}

private fun stageLabel(stage: String): String = when (stage) {
    "queued" -> "排队"
    "analyzing" -> "调用模型"
    "validating" -> "校验输出"
    "loading_plan" -> "获取计划"
    "done" -> "完成"
    "succeeded" -> "完成"
    else -> stage
}

private fun formatDuration(seconds: Int): String = when {
    seconds <= 0 -> "不限时"
    seconds < 60 -> "${seconds} 秒"
    else -> "${seconds / 60} 分 ${seconds % 60} 秒"
}