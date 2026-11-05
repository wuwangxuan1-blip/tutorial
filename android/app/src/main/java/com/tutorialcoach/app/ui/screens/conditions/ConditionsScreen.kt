package com.tutorialcoach.app.ui.screens.conditions

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
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import com.tutorialcoach.app.di.AppContainer
import com.tutorialcoach.app.ui.components.ErrorBanner

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ConditionsScreen(
    container: AppContainer,
    onBack: () -> Unit,
    onOpenRevision: () -> Unit,
) {
    val viewModel: ConditionsViewModel = viewModel(
        factory = viewModelFactory {
            initializer { ConditionsViewModel(container.repository) }
        },
    )
    val state by viewModel.state.collectAsStateWithLifecycle()
    val session by viewModel.session.collectAsStateWithLifecycle()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("修改条件") },
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
            Text(
                "省略字段保持不变；留空不会清空已有值。清空备注会提交 null。",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Text("当前计划版本：${session?.currentPlanVersion ?: "无计划"}")
            OutlinedTextField(
                value = state.timeBudget,
                onValueChange = viewModel::updateTimeBudget,
                label = { Text("时间预算（分钟）") },
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
            )
            OutlinedTextField(
                value = state.people,
                onValueChange = viewModel::updatePeople,
                label = { Text("参与人数") },
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
            )
            OutlinedTextField(
                value = state.servings,
                onValueChange = viewModel::updateServings,
                label = { Text("份量") },
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
            )
            OutlinedTextField(
                value = state.notes,
                onValueChange = viewModel::updateNotes,
                label = { Text("备注（可选）") },
                modifier = Modifier.fillMaxWidth(),
                minLines = 2,
            )

            Button(
                onClick = viewModel::submit,
                enabled = !state.saving,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(52.dp),
            ) {
                Text(if (state.saving) "提交中…" else "提交条件修改")
            }
            OutlinedButton(
                onClick = viewModel::clearNotes,
                enabled = !state.saving,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(52.dp),
            ) {
                Text("清空备注（提交 null）")
            }

            state.error?.let {
                ErrorBanner(
                    message = it,
                    retryable = false,
                    onRetry = null,
                    onDismiss = null,
                )
            }

            state.impact?.let { impact ->
                Card(modifier = Modifier.fillMaxWidth()) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        Text(impact.message, style = MaterialTheme.typography.bodyMedium)
                        Text(
                            "变化字段：${impact.changedFields.joinToString("、").ifBlank { "无" }}",
                            style = MaterialTheme.typography.bodySmall,
                        )
                        if (impact.requiresRevision) {
                            Button(
                                onClick = onOpenRevision,
                                modifier = Modifier.fillMaxWidth(),
                            ) {
                                Text("已有进度，生成条件修订")
                            }
                        }
                        if (impact.requiresRegeneration) {
                            Text(
                                "计划尚未开始；可返回计划页全量重新生成。",
                                style = MaterialTheme.typography.bodySmall,
                            )
                        }
                    }
                }
            }

            state.message?.let {
                Text(it, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.primary)
            }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedButton(onClick = onBack, modifier = Modifier.weight(1f)) {
                    Text("返回计划")
                }
                OutlinedButton(onClick = onOpenRevision, modifier = Modifier.weight(1f)) {
                    Text("查看修订")
                }
            }
        }
    }
}