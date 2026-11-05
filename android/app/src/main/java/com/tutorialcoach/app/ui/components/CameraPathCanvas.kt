package com.tutorialcoach.app.ui.components

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.Card

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Slider
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.runtime.withFrameNanos
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.unit.dp
import com.tutorialcoach.app.domain.CameraEasing
import com.tutorialcoach.app.domain.CameraMoveValidator
import com.tutorialcoach.app.domain.CameraPlaybackState
import com.tutorialcoach.app.domain.DomainCameraMoveSpec
import com.tutorialcoach.app.domain.DomainPoint
import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.sin

@Composable
fun CameraMoveSection(spec: DomainCameraMoveSpec) {
    val errors = remember(spec) { CameraMoveValidator.validate(spec) }
    Card(modifier = Modifier.fillMaxWidth(), shape = RoundedCornerShape(16.dp)) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Text("运镜示意", style = MaterialTheme.typography.titleMedium)
            if (errors.isNotEmpty()) {
                Text(
                    "运镜数据不可用，无法播放动画。",
                    style = MaterialTheme.typography.titleSmall,
                    color = MaterialTheme.colorScheme.error,
                )
                errors.forEach {
                    Text("• $it", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.error)
                }
                return@Column
            }
            Text(
                motionLabel(spec.motionType),
                style = MaterialTheme.typography.titleSmall,
                color = MaterialTheme.colorScheme.primary,
            )
            Text(
                "主体：${spec.subjectAnchor.label} · ${spec.shotType} · ${spec.durationS} 秒 · ${spec.easing}",
                style = MaterialTheme.typography.bodySmall,
            )
            var playback by remember(spec.id) { mutableStateOf(CameraPlaybackState()) }
            LaunchedEffect(playback.playing) {
                var lastFrame = 0L
                while (playback.playing) {
                    withFrameNanos { now ->
                        if (lastFrame != 0L) {
                            playback = playback.tick(
                                deltaSeconds = (now - lastFrame) / 1_000_000_000f,
                                durationS = spec.durationS,
                            )
                        }
                        lastFrame = now
                    }
                }
            }
            Canvas(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(250.dp),
            ) {
                drawRoundRect(
                    color = Color(0xFFF2F2F2),
                    size = size,
                    cornerRadius = androidx.compose.ui.geometry.CornerRadius(18f, 18f),
                )
                val pad = 24f
                val width = size.width - pad * 2
                val height = size.height - pad * 2
                val subject = Offset(
                    pad + (spec.subjectAnchor.x.coerceIn(0.0, 1.0) * width).toFloat(),
                    pad + (spec.subjectAnchor.y.coerceIn(0.0, 1.0) * height).toFloat(),
                )
                val accent = Color(0xFFB5652A)

                fun point(value: DomainPoint): Offset = Offset(
                    pad + (value.x.coerceIn(0.0, 1.0) * width).toFloat(),
                    pad + (value.y.coerceIn(0.0, 1.0) * height).toFloat(),
                )

                drawCircle(Color(0xFF2E6B5E), radius = 26f, center = subject, style = Stroke(width = 5f))
                drawCircle(Color(0xFF2E6B5E), radius = 6f, center = subject)
                val easedProgress = CameraEasing.easedProgress(spec.easing, playback.progress)

                when (spec.motionType) {
                    "camera_move" -> {
                        val path = spec.positionPath ?: return@Canvas
                        val start = point(path.start)
                        val end = point(path.end)
                        val control = path.control?.let(::point)
                            ?: Offset((start.x + end.x) / 2f, (start.y + end.y) / 2f)
                        val line = Path().apply {
                            moveTo(start.x, start.y)
                            quadraticTo(control.x, control.y, end.x, end.y)
                        }
                        drawPath(line, color = accent, style = Stroke(width = 5f))
                        val t = easedProgress
                        val oneMinus = 1f - t
                        val camera = Offset(
                            oneMinus * oneMinus * start.x + 2f * oneMinus * t * control.x + t * t * end.x,
                            oneMinus * oneMinus * start.y + 2f * oneMinus * t * control.y + t * t * end.y,
                        )
                        drawLine(Color(0xFF777777), start = subject, end = camera, strokeWidth = 2f)
                        drawCircle(accent, radius = 12f, center = camera)
                    }
                    "lens_zoom" -> {
                        val zoom = spec.zoom ?: return@Canvas
                        val scale = (zoom.startScale + (zoom.endScale - zoom.startScale) * easedProgress)
                            .coerceAtLeast(0.5)
                        val half = (size.minDimension / (3.2f * scale)).toFloat()
                        drawRect(
                            color = accent,
                            topLeft = Offset(subject.x - half, subject.y - half),
                            size = Size(half * 2, half * 2),
                            style = Stroke(width = 5f),
                        )
                        drawCircle(accent.copy(alpha = 0.55f), radius = half, center = subject, style = Stroke(width = 2f))
                    }
                    "orientation_only" -> {
                        val path = spec.orientationPath ?: return@Canvas
                        val yawDeg = path.startYawDeg + (path.endYawDeg - path.startYawDeg) * easedProgress
                        val pitchDeg = path.startPitchDeg + (path.endPitchDeg - path.startPitchDeg) * easedProgress
                        val yaw = yawDeg * PI / 180.0
                        val radius = 62f + (pitchDeg / 90.0 * 18.0).toFloat()
                        val end = Offset(
                            subject.x + (sin(yaw) * radius).toFloat(),
                            subject.y - (cos(yaw) * radius).toFloat(),
                        )
                        drawLine(accent, start = subject, end = end, strokeWidth = 5f)
                        val left = Offset(end.x - 14f, end.y + 8f)
                        val right = Offset(end.x + 14f, end.y + 8f)
                        drawLine(accent, end = end, start = left, strokeWidth = 4f)
                        drawLine(accent, end = end, start = right, strokeWidth = 4f)
                    }
                    "static" -> {
                        drawCircle(accent, radius = 34f, center = subject, style = Stroke(width = 3f))
                    }
                }
            }
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                if (playback.playing) {
                    Button(onClick = { playback = playback.pause() }) { Text("暂停") }
                } else {
                    Button(onClick = { playback = playback.play() }) { Text("播放") }
                }
                OutlinedButton(onClick = { playback = playback.replay() }) { Text("重播") }
            }
            Slider(
                value = playback.progress,
                onValueChange = { playback = playback.seek(it) },
                valueRange = 0f..1f,
                modifier = Modifier.fillMaxWidth(),
            )
            Text(
                "时间轴 %.1f / %.1f 秒（可拖动）".format(
                    playback.progress * spec.durationS,
                    spec.durationS.toFloat(),
                ),
                style = MaterialTheme.typography.bodySmall,
            )
            Text(
                "2D 俯视/取景示意，不代表真实 3D 轨迹、焦距或景深。",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            spec.limitations.forEach {
                Text("• $it", style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        }
    }
}

private fun motionLabel(motionType: String): String = when (motionType) {
    "camera_move" -> "机位移动"
    "lens_zoom" -> "镜头变焦"
    "orientation_only" -> "原地转向"
    "static" -> "静止机位"
    else -> "未知运镜"
}