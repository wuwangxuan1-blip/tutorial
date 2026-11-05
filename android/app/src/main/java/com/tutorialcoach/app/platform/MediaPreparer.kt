package com.tutorialcoach.app.platform

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.ImageDecoder
import android.media.MediaMetadataRetriever
import android.net.Uri
import android.os.Build
import android.provider.OpenableColumns
import com.tutorialcoach.app.domain.MediaLimits
import java.io.File
import java.io.FileOutputStream

data class PreparedImage(
    val uri: String,
    val file: File,
    val width: Int,
    val height: Int,
)

data class PreparedVideo(
    val uri: String,
    val file: File,
    val durationMs: Long,
    val sizeBytes: Long,
    val thumbnail: File?,
    val mime: String,
)

class MediaValidationException(message: String) : Exception(message)

interface MediaLoader {
    fun prepareImage(uri: String): PreparedImage

    fun prepareVideo(uri: String): PreparedVideo
}

class MediaPreparer(context: Context) : MediaLoader {
    private val appContext = context.applicationContext
    private val resolver = appContext.contentResolver
    private val cacheDir = appContext.cacheDir

    override fun prepareImage(uri: String): PreparedImage {
        val parsed = Uri.parse(uri)
        val bitmap = decodeImage(parsed)
        val longEdge = maxOf(bitmap.width, bitmap.height)
        val scaled = if (longEdge > 2048) {
            val ratio = 2048f / longEdge
            Bitmap.createScaledBitmap(
                bitmap,
                (bitmap.width * ratio).toInt().coerceAtLeast(1),
                (bitmap.height * ratio).toInt().coerceAtLeast(1),
                true,
            )
        } else {
            bitmap
        }
        val file = File.createTempFile("prepared_image_", ".jpg", cacheDir)
        FileOutputStream(file).use { output ->
            if (!scaled.compress(Bitmap.CompressFormat.JPEG, 85, output)) {
                throw MediaValidationException("图片压缩失败，请重新选择。")
            }
        }
        val result = PreparedImage(uri, file, scaled.width, scaled.height)
        if (scaled !== bitmap) scaled.recycle()
        bitmap.recycle()
        return result
    }

    override fun prepareVideo(uri: String): PreparedVideo {
        val parsed = Uri.parse(uri)
        val size = resolveSize(parsed)
        val retriever = MediaMetadataRetriever()
        try {
            retriever.setDataSource(appContext, parsed)
            val duration = retriever.extractMetadata(MediaMetadataRetriever.METADATA_KEY_DURATION)
                ?.toLongOrNull()
            MediaLimits.validateVideo(duration, size)?.let { throw MediaValidationException(it) }
            val mime = resolver.getType(parsed) ?: "video/mp4"
            val extension = if (mime == "video/quicktime") ".mov" else ".mp4"
            val file = File.createTempFile("prepared_video_", extension, cacheDir)
            resolver.openInputStream(parsed)?.use { input ->
                file.outputStream().use { output -> input.copyTo(output) }
            } ?: throw MediaValidationException("无法读取视频文件。")
            val thumbnail = runCatching {
                retriever.getFrameAtTime(0)?.let { frame ->
                    val output = File.createTempFile("video_thumb_", ".jpg", cacheDir)
                    FileOutputStream(output).use { frame.compress(Bitmap.CompressFormat.JPEG, 80, it) }
                    output
                }
            }.getOrNull()
            return PreparedVideo(
                uri = uri,
                file = file,
                durationMs = duration ?: 0L,
                sizeBytes = size ?: file.length(),
                thumbnail = thumbnail,
                mime = mime,
            )
        } finally {
            retriever.release()
        }
    }

    private fun decodeImage(uri: Uri): Bitmap {
        return try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
                val source = ImageDecoder.createSource(resolver, uri)
                ImageDecoder.decodeBitmap(source) { decoder, info, _ ->
                    val longEdge = maxOf(info.size.width, info.size.height)
                    if (longEdge > 2048) {
                        val ratio = 2048f / longEdge
                        decoder.setTargetSize(
                            (info.size.width * ratio).toInt().coerceAtLeast(1),
                            (info.size.height * ratio).toInt().coerceAtLeast(1),
                        )
                    }
                    decoder.allocator = ImageDecoder.ALLOCATOR_SOFTWARE
                }
            } else {
                resolver.openInputStream(uri)?.use { input ->
                    BitmapFactory.decodeStream(input)
                } ?: throw MediaValidationException("无法读取图片。")
            }
        } catch (error: Exception) {
            throw MediaValidationException("图片无法解码（HEIC 请先转 JPEG），请换一张图片。")
        } ?: throw MediaValidationException("图片无法解码，请换一张图片。")
    }

    private fun resolveSize(uri: Uri): Long? {
        resolver.openAssetFileDescriptor(uri, "r")?.use { descriptor ->
            if (descriptor.length > 0) return descriptor.length
        }
        resolver.query(uri, arrayOf(OpenableColumns.SIZE), null, null, null)?.use { cursor ->
            if (cursor.moveToFirst()) {
                val index = cursor.getColumnIndex(OpenableColumns.SIZE)
                if (index >= 0 && !cursor.isNull(index)) return cursor.getLong(index)
            }
        }
        return null
    }
}