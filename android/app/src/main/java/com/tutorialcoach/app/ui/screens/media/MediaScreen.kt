package com.tutorialcoach.app.ui.screens.media

import android.graphics.BitmapFactory
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.PickVisualMediaRequest
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.Checkbox
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import com.tutorialcoach.app.di.AppContainer
import com.tutorialcoach.app.domain.DomainFeedback
import com.tutorialcoach.app.platform.MediaPreparer
import com.tutorialcoach.app.ui.components.ErrorBanner
import java.io.File

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MediaScreen(
    container: AppContainer,
    onBack: () -> Unit,
) {
    val context = LocalContext.current
    val viewModel: MediaViewModel = viewModel(
        factory = viewModelFactory {
            initializer {
                MediaViewModel(
                    container.repository,
                    container.repository,
                    MediaPreparer(context.applicationContext),
                )
            }
        },
    )
    val state by viewModel.state.collectAsStateWithLifecycle()
    val session by viewModel.session.collectAsStateWithLifecycle()
    val plan by viewModel.plan.collectAsStateWithLifecycle()
    val progress by viewModel.progress.collectAsStateWithLifecycle()

    val imagePicker = rememberLauncherForActivityResult(
        ActivityResultContracts.PickMultipleVisualMedia(4),
    ) { uris ->
        viewModel.addImages(uris.map { it.toString() })
    }
    val videoPicker = rememberLauncherForActivityResult(
        ActivityResultContracts.PickVisualMedia(),
    ) { uri ->
        uri?.let { viewModel.setVideo(it.toString()) }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("照片 / 短片反馈") },
                navigationIcon = { TextButton(onClick = onBack) { Text("返回") } },
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
            Text("当前步骤：${session?.currentPlanVersion?.let { "计划 v$it" } ?: "无计划"}", style = MaterialTheme.typography.labelLarge)
            val currentStep = plan?.steps?.firstOrNull { it.id == progress.currentStepId }
                ?: plan?.steps?.firstOrNull()
            Text(
                currentStep?.let { "当前步骤：${it.title}" } ?: "请先在步骤卡生成计划",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )

            Card(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("隐私提示", style = MaterialTheme.typography.titleSmall)
                    Text(
                        "媒体只上传到你配置的本地服务端，用于本次步骤反馈；不分析音频、不转写声音。服务端会去除图片 EXIF，视频仅抽取少量帧。图片/短片不会进入 APK 或 Git。",
                        style = MaterialTheme.typography.bodySmall,
                    )
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Checkbox(
                            checked = state.privacyAccepted,
                            onCheckedChange = viewModel::setPrivacyAccepted,
                        )
                        Text("我已阅读并同意上述隐私提示", modifier = Modifier.padding(top = 12.dp))
                    }
                }
            }

            Row(horizontalArrangement = Arrangement.spacedBy(12.dp), modifier = Modifier.fillMaxWidth()) {
                OutlinedButton(
                    onClick = {
                        imagePicker.launch(
                            PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageOnly),
                        )
                    },
                    modifier = Modifier
                        .weight(1f)
                        .height(52.dp),
                ) {
                    Text("选择照片")
                }
                OutlinedButton(
                    onClick = {
                        videoPicker.launch(
                            PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.VideoOnly),
                        )
                    },
                    modifier = Modifier
                        .weight(1f)
                        .height(52.dp),
                ) {
                    Text("选择短片")
                }
            }
            Text(
                "图片 1–4 张，每张 ≤10 MiB；短片 1 段，≤30 秒且 ≤100 MiB。选择不申请存储权限。",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )

            state.images.forEach { image ->
                Card(modifier = Modifier.fillMaxWidth()) {
                    Row(
                        modifier = Modifier.padding(10.dp),
                        horizontalArrangement = Arrangement.spacedBy(12.dp),
                    ) {
                        LocalImage(image.file, modifier = Modifier.size(96.dp))
                        Column(modifier = Modifier.weight(1f)) {
                            Text("图片 ${image.width}×${image.height}", style = MaterialTheme.typography.bodyMedium)
                            Text(
                                "${"%.1f".format(image.file.length() / 1024f / 1024f)} MiB · 已压缩为 JPEG",
                                style = MaterialTheme.typography.bodySmall,
                            )
                            TextButton(onClick = { viewModel.removeImage(image) }) { Text("移除") }
                        }
                    }
                }
            }

            state.video?.let { video ->
                Card(modifier = Modifier.fillMaxWidth()) {
                    Row(
                        modifier = Modifier.padding(10.dp),
                        horizontalArrangement = Arrangement.spacedBy(12.dp),
                    ) {
                        video.thumbnail?.let { LocalImage(it, modifier = Modifier.size(96.dp)) }
                        Column(modifier = Modifier.weight(1f)) {
                            Text("短片", style = MaterialTheme.typography.bodyMedium)
                            Text(
                                "%.1f 秒 · %.1f MiB · 音频不分析".format(
                                    video.durationMs / 1000.0,
                                    video.sizeBytes / 1024.0 / 1024.0,
                                ),
                                style = MaterialTheme.typography.bodySmall,
                            )
                            TextButton(onClick = viewModel::clearMedia) { Text("移除") }
                        }
                    }
                }
            }

            OutlinedTextField(
                value = state.note,
                onValueChange = viewModel::updateNote,
                label = { Text("补充说明（可选，≤500 字）") },
                modifier = Modifier.fillMaxWidth(),
                minLines = 2,
            )

            if (state.uploading) {
                LinearProgressIndicator(
                    progress = { state.uploadProgress },
                    modifier = Modifier.fillMaxWidth(),
                )
                Text("上传中 ${(state.uploadProgress * 100).toInt()}%", style = MaterialTheme.typography.bodySmall)
            }

            Button(
                onClick = viewModel::submit,
                enabled = !state.submitting && (state.images.isNotEmpty() || state.video != null),
                modifier = Modifier
                    .fillMaxWidth()
                    .height(52.dp),
            ) {
                Text(if (state.submitting) "分析中…" else "上传并请求反馈")
            }

            state.message?.let {
                Text(it, color = MaterialTheme.colorScheme.primary, style = MaterialTheme.typography.bodyMedium)
            }
            state.error?.let {
                ErrorBanner(
                    message = it,
                    retryable = state.retryable,
                    onRetry = viewModel::retry,
                    onDismiss = viewModel::dismissError,
                )
            }

            state.feedback?.let { feedback ->
                FeedbackCard(feedback, state, viewModel)
            }

            OutlinedButton(onClick = onBack, modifier = Modifier.fillMaxWidth()) { Text("返回步骤") }
        }
    }
}

@Composable
private fun FeedbackCard(
    feedback: DomainFeedback,
    state: MediaUiState,
    viewModel: MediaViewModel,
) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text("媒体反馈", style = MaterialTheme.typography.titleMedium)
            Text("评估：${assessmentLabel(feedback.assessment)}", style = MaterialTheme.typography.labelLarge)
            Text(feedback.summary, style = MaterialTheme.typography.bodyMedium)
            feedback.observations.forEach { observation ->
                val evidence = observation.evidence
                val label = if (evidence.kind == "video_frame") {
                    "视频帧 ${evidence.frameIndex} · ${"%.1f".format(evidence.timestampS ?: 0.0)}s"
                } else {
                    "图片证据"
                }
                Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                    EvidenceThumbnail(state, evidence.mediaId, Modifier.size(72.dp))
                    Column(modifier = Modifier.weight(1f)) {
                        Text(observation.text, style = MaterialTheme.typography.bodyMedium)
                        Text("$label · 把握：${certaintyLabel(observation.certainty)}", style = MaterialTheme.typography.bodySmall)
                    }
                }
            }
            if (feedback.observations.isEmpty()) {
                Text("没有可引用本次媒体的观察，结论为不明确。", style = MaterialTheme.typography.bodySmall)
            }
            if (feedback.uncertainties.isNotEmpty()) {
                Text("不确定项", style = MaterialTheme.typography.titleSmall)
                feedback.uncertainties.forEach { Text("• $it", style = MaterialTheme.typography.bodySmall) }
            }
            if (feedback.limitations.isNotEmpty()) {
                Text("局限", style = MaterialTheme.typography.titleSmall)
                feedback.limitations.forEach { Text("• $it", style = MaterialTheme.typography.bodySmall) }
            }
            feedback.motionMetrics?.let { metrics ->
                Text(
                    "运动指标：${metrics.method} · ${metrics.frameCount} 帧 · 平均平移 ${metrics.meanTranslationPx}px · 平均旋转 ${metrics.meanRotationDeg}°",
                    style = MaterialTheme.typography.bodySmall,
                )
                metrics.limitations.forEach { Text("• $it", style = MaterialTheme.typography.bodySmall) }
            }
            Text(feedback.audioNote, style = MaterialTheme.typography.bodySmall)
            if (feedback.suggestedActions.isNotEmpty()) {
                Text("建议动作", style = MaterialTheme.typography.titleSmall)
                feedback.suggestedActions.forEach { Text("• $it", style = MaterialTheme.typography.bodySmall) }
            }
            if (feedback.followUpQuestions.isNotEmpty()) {
                Text("可以继续回答", style = MaterialTheme.typography.titleSmall)
                feedback.followUpQuestions.forEach { Text("• $it", style = MaterialTheme.typography.bodySmall) }
            }
            TextButton(onClick = viewModel::clearMedia) { Text("清空媒体，重新提交") }
        }
    }
}

@Composable
private fun EvidenceThumbnail(state: MediaUiState, mediaId: String, modifier: Modifier = Modifier) {
    val file = remember(state.uploaded, state.images, state.video, mediaId) {
        state.images.forEachIndexed { index, image ->
            if (state.uploaded["image_$index"]?.id == mediaId) return@remember image.file
        }
        if (state.uploaded["video"]?.id == mediaId) state.video?.thumbnail
        else null
    }
    if (file != null) {
        LocalImage(file, modifier)
    } else {
        Text("媒体 $mediaId", style = MaterialTheme.typography.bodySmall)
    }
}

@Composable
private fun LocalImage(file: File, modifier: Modifier = Modifier) {
    val bitmap = remember(file.absolutePath, file.lastModified()) {
        BitmapFactory.decodeFile(file.absolutePath)?.asImageBitmap()
    }
    if (bitmap != null) {
        Image(
            bitmap = bitmap,
            contentDescription = "媒体预览",
            modifier = modifier,
            contentScale = ContentScale.Crop,
        )
    } else {
        Text("预览不可用", style = MaterialTheme.typography.bodySmall, modifier = modifier)
    }
}

private fun assessmentLabel(value: String): String = when (value) {
    "likely_met" -> "可能达成（未验证）"
    "not_met" -> "可能未达成"
    "unclear" -> "不明确"
    "not_verified" -> "未验证"
    else -> value
}

private fun certaintyLabel(value: String): String = when (value) {
    "high" -> "高（模型自评）"
    "medium" -> "中（模型自评）"
    "low" -> "低（模型自评）"
    else -> value
}