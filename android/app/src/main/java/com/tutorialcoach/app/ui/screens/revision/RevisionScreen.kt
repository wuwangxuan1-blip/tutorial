package com.tutorialcoach.app.ui.screens.revision

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
import com.tutorialcoach.app.domain.DomainRevision
import com.tutorialcoach.app.ui.components.ErrorBanner

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RevisionScreen(
    container: AppContainer,
    onBack: () -> Unit,
) {
    val viewModel: RevisionViewModel = viewModel(
        factory = viewModelFactory {
            initializer { RevisionViewModel(container.repository) }
        },
    )
    val state by viewModel.state.collectAsStateWithLifecycle()
    val session by viewModel.session.collectAsStateWithLifecycle()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("修订提案") },
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
                "条件修订只调整未完成步骤；已完成/已跳过步骤不会被修改。",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Text("当前计划版本：${session?.currentPlanVersion ?: "无计划"}")

            OutlinedTextField(
                value = state.reason,
                onValueChange = viewModel::updateReason,
                label = { Text("修订原因（1–300 字）") },
                modifier = Modifier.fillMaxWidth(),
                minLines = 2,
            )
            Button(
                onClick = viewModel::createRevision,
                enabled = !state.submitting,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(52.dp),
            ) {
                Text(if (state.submitting) "生成中…" else "生成条件修订提案")
            }

            state.error?.let {
                ErrorBanner(
                    message = it,
                    retryable = true,
                    onRetry = viewModel::load,
                    onDismiss = null,
                )
            }
            state.message?.let {
                Text(it, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.primary)
            }
            if (state.loading) {
                Text("正在加载修订提案…")
            }

            state.revisions.forEach { revision ->
                RevisionCard(
                    revision = revision,
                    submitting = state.submitting,
                    onApply = { viewModel.apply(revision) },
                    onReject = { viewModel.reject(revision) },
                )
            }
            if (state.revisions.isEmpty() && !state.loading) {
                Text("暂无修订提案。")
            }
            OutlinedButton(onClick = onBack, modifier = Modifier.fillMaxWidth()) {
                Text("返回计划")
            }
        }
    }
}

@Composable
private fun RevisionCard(
    revision: DomainRevision,
    submitting: Boolean,
    onApply: () -> Unit,
    onReject: () -> Unit,
) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text("修订 ${revision.id}", style = MaterialTheme.typography.titleSmall)
            Text("状态：${revision.status} · 基于版本 v${revision.basePlanVersion}")
            revision.requestReason?.let {
                Text("原因：$it", style = MaterialTheme.typography.bodySmall)
            }
            revision.changes.forEach { change ->
                Text(
                    "变更 ${change.op} ${change.stepId ?: ""}",
                    style = MaterialTheme.typography.bodyMedium,
                )
                if (change.before.isNotEmpty()) {
                    change.before.forEach { (key, value) ->
                        Text("前 $key：$value", style = MaterialTheme.typography.bodySmall)
                    }
                }
                change.after.forEach { (key, value) ->
                    Text("后 $key：$value", style = MaterialTheme.typography.bodySmall)
                }
                Text(
                    "说明：${change.reason}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
            if (revision.status == "proposed") {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Button(onClick = onApply, enabled = !submitting, modifier = Modifier.weight(1f)) {
                        Text("应用")
                    }
                    OutlinedButton(onClick = onReject, enabled = !submitting, modifier = Modifier.weight(1f)) {
                        Text("拒绝")
                    }
                }
            }
        }
    }
}