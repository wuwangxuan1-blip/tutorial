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
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.tutorialcoach.app.di.AppContainer
import com.tutorialcoach.app.domain.DomainStep

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun StepScreen(
    container: AppContainer,
    onBack: () -> Unit,
) {
    val plan by container.repository.plan.collectAsStateWithLifecycle()
    var index by rememberSaveable { mutableIntStateOf(0) }

    LaunchedEffect(plan?.id) {
        index = 0
    }

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
        val currentPlan = plan
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(20.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            if (currentPlan == null) {
                Text("还没有计划，请先在计划页生成。")
                return@Column
            }
            Text(
                text = "只读步骤卡：本阶段不包含计时、完成标记和媒体反馈。查看步骤不代表模型已验证完成。",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Text(currentPlan.title, style = MaterialTheme.typography.titleLarge)
            Text(
                text = "第 ${index + 1} / ${currentPlan.steps.size} 步",
                style = MaterialTheme.typography.labelLarge,
                color = MaterialTheme.colorScheme.primary,
            )
            val step = currentPlan.steps.getOrNull(index)
            if (step == null) {
                Text("步骤数据为空。")
                return@Column
            }

            StepContentCard(step)

            Row(
                horizontalArrangement = Arrangement.spacedBy(12.dp),
                modifier = Modifier.fillMaxWidth(),
            ) {
                OutlinedButton(
                    onClick = { if (index > 0) index -= 1 },
                    enabled = index > 0,
                    modifier = Modifier
                        .weight(1f)
                        .height(52.dp),
                ) {
                    Text("上一步")
                }
                Button(
                    onClick = { if (index < currentPlan.steps.lastIndex) index += 1 },
                    enabled = index < currentPlan.steps.lastIndex,
                    modifier = Modifier
                        .weight(1f)
                        .height(52.dp),
                ) {
                    Text("下一步")
                }
            }
            if (index == currentPlan.steps.lastIndex) {
                Text(
                    text = "已是最后一步。完成状态与结果记录将在后续阶段实现。",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
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
                step.completionCriteria.forEach { Text("• $it", style = MaterialTheme.typography.bodyMedium) }
            }
            if (step.safety.isNotEmpty()) {
                Section(title = "安全提示") {
                    step.safety.forEach { Text("• $it", style = MaterialTheme.typography.bodyMedium) }
                }
            }
            if (step.commonMistakes.isNotEmpty()) {
                Section(title = "常见错误") {
                    step.commonMistakes.forEach { Text("• $it", style = MaterialTheme.typography.bodyMedium) }
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