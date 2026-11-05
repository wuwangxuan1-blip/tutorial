package com.tutorialcoach.app.ui.screens.step

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
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
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
import com.tutorialcoach.app.domain.DomainStep
import com.tutorialcoach.app.domain.DomainTimer
import com.tutorialcoach.app.ui.components.ErrorBanner

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun StepScreen(
    container: AppContainer,
    onBack: () -> Unit,
    onOpenConditions: () -> Unit,
    onOpenRevision: () -> Unit,
) {
    val session by container.repository.session.collectAsStateWithLifecycle()
    val viewModel: StepViewModel = viewModel(
        key = session?.id ?: "no-session",
        factory = viewModelFactory {
            initializer { StepViewModel(container.repository, container.localStore) }
        },
    )
    val plan by viewModel.plan.collectAsStateWithLifecycle()
    val progress by viewModel.progress.collectAsStateWithLifecycle()
    val state by viewModel.state.collectAsStateWithLifecycle()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("步骤卡") },
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
            val currentPlan = plan
            if (currentPlan == null) {
                Text("还没有计划，请先在计划页生成。")
                return@Column
            }
            Text(currentPlan.title, style = MaterialTheme.typography.titleLarge)
            Text(
                text = "用户点完成只记录 self_reported；查看步骤或点下一步不代表模型验证完成。",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Text(
                text = "第 ${state.index + 1} / ${currentPlan.steps.size} 步",
                style = MaterialTheme.typography.labelLarge,
                color = MaterialTheme.colorScheme.primary,
            )
            val step = currentPlan.steps.getOrNull(state.index)
            if (step == null) {
                Text("步骤数据为空。")
                return@Column
            }
            val status = progress.stepStatuses[step.id] ?: "not_started"
            val evidence = progress.evidenceLevels[step.id] ?: "none"
            Text(
                text = "状态：${statusLabel(status)} · 证据：${evidenceLabel(evidence)}",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )

            StepContentCard(step)

            TimerCard(
                timer = state.timer,
                remainingSeconds = state.timerRemainingS,
                onStart = viewModel::startTimer,
                onPause = viewModel::pauseTimer,
                onResume = viewModel::resumeTimer,
                onReset = viewModel::resetTimer,
            )

            if (state.timerNeedsConfirmation) {
                Card(modifier = Modifier.fillMaxWidth()) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        Text("计时器可能已失效", style = MaterialTheme.typography.titleSmall)
                        Text(
                            text = "设备重启或时钟变化后，不能确认剩余时间。请选择继续计时或重置；不会出现负计时。",
                            style = MaterialTheme.typography.bodySmall,
                        )
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            OutlinedButton(onClick = viewModel::confirmTimerReset) {
                                Text("重置计时")
                            }
                            Button(onClick = viewModel::confirmTimerContinue) {
                                Text("继续计时")
                            }
                        }
                    }
                }
            }

            Row(
                horizontalArrangement = Arrangement.spacedBy(12.dp),
                modifier = Modifier.fillMaxWidth(),
            ) {
                OutlinedButton(
                    onClick = viewModel::previous,
                    enabled = state.index > 0 && !state.saving,
                    modifier = Modifier
                        .weight(1f)
                        .height(52.dp),
                ) {
                    Text("上一步")
                }
                Button(
                    onClick = viewModel::next,
                    enabled = state.index < currentPlan.steps.lastIndex && !state.saving,
                    modifier = Modifier
                        .weight(1f)
                        .height(52.dp),
                ) {
                    Text("下一步")
                }
            }

            Row(horizontalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxWidth()) {
                Button(
                    onClick = viewModel::completeStep,
                    enabled = status != "done" && status != "skipped" && !state.saving,
                    modifier = Modifier
                        .weight(1f)
                        .height(52.dp),
                ) {
                    Text("完成本步")
                }
                OutlinedButton(
                    onClick = viewModel::skipStep,
                    enabled = status != "done" && status != "skipped" && !state.saving,
                    modifier = Modifier
                        .weight(1f)
                        .height(52.dp),
                ) {
                    Text("跳过本步")
                }
            }

            OutlinedButton(
                onClick = viewModel::saveProgress,
                enabled = !state.saving,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(52.dp),
            ) {
                Text(if (state.saving) "保存中…" else "保存进度")
            }

            Row(horizontalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxWidth()) {
                OutlinedButton(
                    onClick = onOpenConditions,
                    modifier = Modifier
                        .weight(1f)
                        .height(52.dp),
                ) {
                    Text("修改条件")
                }
                OutlinedButton(
                    onClick = onOpenRevision,
                    modifier = Modifier
                        .weight(1f)
                        .height(52.dp),
                ) {
                    Text("修订提案")
                }
            }

            if (session?.status == "paused") {
                Button(
                    onClick = viewModel::resumeSession,
                    enabled = !state.saving,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(52.dp),
                ) {
                    Text("恢复练习")
                }
            } else {
                OutlinedButton(
                    onClick = viewModel::pauseSession,
                    enabled = !state.saving,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(52.dp),
                ) {
                    Text("暂停练习")
                }
            }

            if (session?.status == "in_progress" || session?.status == "paused") {
                Button(
                    onClick = viewModel::completeSession,
                    enabled = !state.saving,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(52.dp),
                ) {
                    Text("完成练习（用户自报）")
                }
            }

            state.message?.let {
                Text(it, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.primary)
            }

            state.error?.let { message ->
                ErrorBanner(
                    message = message,
                    retryable = state.retryable,
                    onRetry = null,
                    onDismiss = viewModel::dismissError,
                )
            }

            AskSection(
                state = state,
                onTextChange = viewModel::updateAskText,
                onAsk = viewModel::ask,
            )
        }
    }
}

@Composable
private fun TimerCard(
    timer: DomainTimer?,
    remainingSeconds: Int,
    onStart: () -> Unit,
    onPause: () -> Unit,
    onResume: () -> Unit,
    onReset: () -> Unit,
) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text("计时器", style = MaterialTheme.typography.titleSmall)
            if (timer == null) {
                Text("未开始计时。", style = MaterialTheme.typography.bodyMedium)
                Button(onClick = onStart) { Text("开始计时") }
                return@Column
            }
            Text(
                text = "${stateLabel(timer.state)} · ${formatClock(remainingSeconds)} / ${formatClock(timer.durationS)}",
                style = MaterialTheme.typography.bodyLarge,
            )
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                when (timer.state) {
                    "running" -> Button(onClick = onPause) { Text("暂停计时") }
                    "paused", "idle" -> Button(onClick = onResume) { Text("继续计时") }
                    else -> Button(onClick = onStart) { Text("重新开始") }
                }
                OutlinedButton(onClick = onReset) { Text("重置") }
            }
        }
    }
}

@Composable
private fun AskSection(
    state: StepUiState,
    onTextChange: (String) -> Unit,
    onAsk: () -> Unit,
) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text("随时提问", style = MaterialTheme.typography.titleSmall)
            Text(
                "回答只基于文字上下文，不判断食物内部温度/食用安全，也不执行命令。",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            OutlinedTextField(
                value = state.askText,
                onValueChange = onTextChange,
                label = { Text("关于当前步骤的问题（≤500 字）") },
                modifier = Modifier.fillMaxWidth(),
                minLines = 2,
            )
            Button(
                onClick = onAsk,
                enabled = state.ask !is AskUiState.Sending,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text(if (state.ask is AskUiState.Sending) "提问中…" else "发送问题")
            }
            when (val ask = state.ask) {
                is AskUiState.Answer -> {
                    Text(ask.value.answer, style = MaterialTheme.typography.bodyMedium)
                    if (ask.value.citations.isNotEmpty()) {
                        Text(
                            "引用：${ask.value.citations.joinToString("、")}",
                            style = MaterialTheme.typography.bodySmall,
                        )
                    }
                    ask.value.limitations.forEach {
                        Text(
                            "局限：$it",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }
                AskUiState.Sending -> Text("正在等待模型回答…", style = MaterialTheme.typography.bodySmall)
                AskUiState.Idle -> Unit
            }
        }
    }
}

@Composable
private fun StepContentCard(step: DomainStep) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(18.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Text(step.title, style = MaterialTheme.typography.headlineSmall)
            Text(
                text = "${phaseLabel(step.phase)} · ${formatDuration(step.durationS)}",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Text(step.instruction, style = MaterialTheme.typography.bodyLarge)
            if (step.why.isNotBlank()) {
                Section(title = "为什么这样做") {
                    Text(step.why, style = MaterialTheme.typography.bodyMedium)
                }
            }
            Section(title = "可观察完成标准") {
                step.completionCriteria.forEach {
                    Text("• $it", style = MaterialTheme.typography.bodyMedium)
                }
            }
            if (step.safety.isNotEmpty()) {
                Section(title = "安全提示") {
                    step.safety.forEach { Text("• $it", style = MaterialTheme.typography.bodyMedium) }
                }
            }
            if (step.commonMistakes.isNotEmpty()) {
                Section(title = "常见错误") {
                    step.commonMistakes.forEach {
                        Text("• $it", style = MaterialTheme.typography.bodyMedium)
                    }
                }
            }
            if (step.evidenceHint.isNotBlank()) {
                Section(title = "可提供的证据") {
                    Text(step.evidenceHint, style = MaterialTheme.typography.bodyMedium)
                }
            }
            if (step.mediaPrompt.isNotBlank()) {
                Text(
                    text = step.mediaPrompt,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}

@Composable
private fun Section(title: String, content: @Composable () -> Unit) {
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Text(title, style = MaterialTheme.typography.titleSmall)
        content()
    }
}

private fun phaseLabel(phase: String): String = when (phase) {
    "prepare" -> "准备"
    "execute" -> "执行"
    "verify" -> "验证"
    "finish" -> "收尾"
    else -> phase
}

private fun formatDuration(seconds: Int): String = when {
    seconds <= 0 -> "不限时"
    seconds < 60 -> "${seconds} 秒"
    else -> "${seconds / 60} 分 ${seconds % 60} 秒"
}

private fun formatClock(seconds: Int): String {
    val safe = seconds.coerceAtLeast(0)
    return "%d:%02d".format(safe / 60, safe % 60)
}

private fun statusLabel(status: String): String = when (status) {
    "not_started" -> "未开始"
    "in_progress" -> "进行中"
    "done" -> "已完成"
    "skipped" -> "已跳过"
    else -> status
}

private fun evidenceLabel(level: String): String = when (level) {
    "none" -> "未提供"
    "self_reported" -> "用户自报（未验证）"
    "media_submitted" -> "已上传媒体"
    "model_observed" -> "模型观察"
    "measured" -> "已测量"
    "not_verifiable" -> "不可验证"
    else -> level
}

private fun stateLabel(state: String): String = when (state) {
    "running" -> "计时中"
    "paused" -> "已暂停"
    "finished" -> "已结束"
    "idle" -> "未开始"
    else -> state
}