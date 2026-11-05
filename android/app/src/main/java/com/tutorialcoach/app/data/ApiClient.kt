package com.tutorialcoach.app.data

import java.io.File
import java.io.IOException
import java.util.UUID
import java.util.concurrent.TimeUnit
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.DeserializationStrategy
import kotlinx.serialization.builtins.ListSerializer
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.encodeToJsonElement
import kotlinx.serialization.json.put
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response
import okio.BufferedSink

class ApiException(
    val code: String,
    override val message: String,
    val retryable: Boolean = false,
    val requestId: String? = null,
    val retryAfterS: Int? = null,
) : Exception(message)

class NetworkException(
    message: String,
    cause: Throwable? = null,
) : Exception(message, cause)

class ApiClient(
    private val baseUrl: String,
) {
    private val json = Json {
        ignoreUnknownKeys = true
        explicitNulls = false
        encodeDefaults = true
    }
    private val contentType = "application/json; charset=utf-8".toMediaType()
    private val client = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)
        .writeTimeout(60, TimeUnit.SECONDS)
        .build()
    private val pollClient = client.newBuilder()
        .readTimeout(15, TimeUnit.SECONDS)
        .build()
    private val askClient = client.newBuilder()
        .readTimeout(75, TimeUnit.SECONDS)
        .build()
    private val uploadClient = client.newBuilder()
        .readTimeout(180, TimeUnit.SECONDS)
        .writeTimeout(180, TimeUnit.SECONDS)
        .build()

    suspend fun health(): HealthDto = getJson("/v1/health", HealthDto.serializer())

    suspend fun capabilities(): CapabilitiesDto = getJson("/v1/capabilities", CapabilitiesDto.serializer())

    suspend fun createSession(request: CreateSessionRequest): SessionDto {
        val body = json.encodeToString(CreateSessionRequest.serializer(), request)
        return postJson(
            path = "/v1/sessions",
            body = body,
            serializer = SessionDto.serializer(),
            idempotencyKey = UUID.randomUUID().toString(),
        )
    }

    suspend fun getSession(sessionId: String): SessionDto = getJson(
        path = "/v1/sessions/$sessionId",
        serializer = SessionDto.serializer(),
    )

    suspend fun submitAnswers(sessionId: String, answers: List<AnswerDto>): SessionDto {
        val body = json.encodeToString(
            AnswerSubmissionDto.serializer(),
            AnswerSubmissionDto(answers),
        )
        return postJson(
            path = "/v1/sessions/$sessionId/answers",
            body = body,
            serializer = SessionDto.serializer(),
            idempotencyKey = UUID.randomUUID().toString(),
        )
    }

    suspend fun createPlanJob(
        sessionId: String,
        basePlanVersion: Int?,
        idempotencyKey: String,
    ): JobDto {
        val body = json.encodeToString(
            CreatePlanJobRequest.serializer(),
            CreatePlanJobRequest(basePlanVersion),
        )
        return postJson(
            path = "/v1/sessions/$sessionId/plan-jobs",
            body = body,
            serializer = JobDto.serializer(),
            idempotencyKey = idempotencyKey,
        )
    }

    suspend fun getJob(jobId: String): JobDto = getJson(
        path = "/v1/jobs/$jobId",
        serializer = JobDto.serializer(),
        readClient = pollClient,
    )

    suspend fun getPlan(sessionId: String): PlanDto = getJson(
        path = "/v1/sessions/$sessionId/plan",
        serializer = PlanDto.serializer(),
    )

    suspend fun updateProgress(sessionId: String, update: ProgressUpdate): ProgressResponseDto {
        val body = buildJsonObject {
            put("base_plan_version", update.basePlanVersion)
            if (update.includeCurrentStep) {
                put(
                    "current_step_id",
                    update.currentStepId?.let { JsonPrimitive(it) } ?: JsonNull,
                )
            }
            update.stepStatuses?.let { statuses ->
                put("step_statuses", buildJsonObject {
                    statuses.forEach { (stepId, status) -> put(stepId, JsonPrimitive(status)) }
                })
            }
            update.evidenceLevels?.let { levels ->
                put("evidence_levels", buildJsonObject {
                    levels.forEach { (stepId, level) -> put(stepId, JsonPrimitive(level)) }
                })
            }
            if (update.includeTimer) {
                put(
                    "timer",
                    update.timer?.let {
                        json.encodeToJsonElement(TimerDto.serializer(), it)
                    } ?: JsonNull,
                )
            }
        }
        return patchJson(
            path = "/v1/sessions/$sessionId/progress",
            body = body.toString(),
            serializer = ProgressResponseDto.serializer(),
        )
    }

    suspend fun pauseSession(sessionId: String): SessionDto = postJson(
        path = "/v1/sessions/$sessionId/pause",
        body = "{}",
        serializer = SessionDto.serializer(),
        idempotencyKey = UUID.randomUUID().toString(),
    )

    suspend fun resumeSession(sessionId: String): SessionDto = postJson(
        path = "/v1/sessions/$sessionId/resume",
        body = "{}",
        serializer = SessionDto.serializer(),
        idempotencyKey = UUID.randomUUID().toString(),
    )

    suspend fun completeSession(
        sessionId: String,
        rating: Int?,
        notes: String,
    ): CompleteResponseDto {
        val body = json.encodeToString(
            CompleteRequestDto.serializer(),
            CompleteRequestDto(rating, notes),
        )
        return postJson(
            path = "/v1/sessions/$sessionId/complete",
            body = body,
            serializer = CompleteResponseDto.serializer(),
            idempotencyKey = UUID.randomUUID().toString(),
        )
    }

    suspend fun ask(
        sessionId: String,
        question: String,
        stepId: String,
        planVersion: Int,
    ): AskResponseDto {
        val body = json.encodeToString(
            AskRequestDto.serializer(),
            AskRequestDto(question, stepId, planVersion),
        )
        return postJson(
            path = "/v1/sessions/$sessionId/ask",
            body = body,
            serializer = AskResponseDto.serializer(),
            idempotencyKey = UUID.randomUUID().toString(),
            readClient = askClient,
        )
    }

    suspend fun patchConditions(
        sessionId: String,
        basePlanVersion: Int?,
        conditions: Map<String, JsonElement?>,
    ): ConditionsPatchResponseDto {
        val body = buildJsonObject {
            if (basePlanVersion != null) {
                put("base_plan_version", basePlanVersion)
            }
            put("conditions", buildJsonObject {
                conditions.forEach { (field, value) ->
                    put(field, value ?: JsonNull)
                }
            })
        }
        return patchJson(
            path = "/v1/sessions/$sessionId/conditions",
            body = body.toString(),
            serializer = ConditionsPatchResponseDto.serializer(),
        )
    }

    suspend fun createRevisionJob(
        sessionId: String,
        basePlanVersion: Int,
        requestReason: String,
        idempotencyKey: String,
    ): JobDto {
        val body = json.encodeToString(
            RevisionJobRequestDto.serializer(),
            RevisionJobRequestDto(
                feedbackId = null,
                basePlanVersion = basePlanVersion,
                requestReason = requestReason,
            ),
        )
        return postJson(
            path = "/v1/sessions/$sessionId/revision-jobs",
            body = body,
            serializer = JobDto.serializer(),
            idempotencyKey = idempotencyKey,
        )
    }

    suspend fun listRevisions(sessionId: String): List<RevisionDto> = getJson(
        path = "/v1/sessions/$sessionId/revisions",
        serializer = ListSerializer(RevisionDto.serializer()),
    )

    suspend fun applyRevision(
        sessionId: String,
        revisionId: String,
        basePlanVersion: Int,
    ): RevisionApplyResponseDto {
        val body = json.encodeToString(
            RevisionApplyRequestDto.serializer(),
            RevisionApplyRequestDto(basePlanVersion),
        )
        return postJson(
            path = "/v1/sessions/$sessionId/revisions/$revisionId/apply",
            body = body,
            serializer = RevisionApplyResponseDto.serializer(),
            idempotencyKey = UUID.randomUUID().toString(),
        )
    }

    suspend fun rejectRevision(
        sessionId: String,
        revisionId: String,
        reason: String,
    ): RevisionDto {
        val body = json.encodeToString(
            RevisionRejectRequestDto.serializer(),
            RevisionRejectRequestDto(reason),
        )
        return postJson(
            path = "/v1/sessions/$sessionId/revisions/$revisionId/reject",
            body = body,
            serializer = RevisionDto.serializer(),
            idempotencyKey = UUID.randomUUID().toString(),
        )
    }

    suspend fun uploadMedia(
        file: File,
        mime: String,
        kind: String,
        onProgress: (Float) -> Unit,
    ): MediaDto = withContext(Dispatchers.IO) {
        val body = MultipartBody.Builder()
            .setType(MultipartBody.FORM)
            .addFormDataPart("kind", kind)
            .addFormDataPart(
                "file",
                file.name,
                ProgressRequestBody(file, mime.toMediaType(), onProgress),
            )
            .build()
        val request = Request.Builder()
            .url("$baseUrl/v1/media")
            .header("Accept", "application/json")
            .header("Idempotency-Key", UUID.randomUUID().toString())
            .post(body)
            .build()
        execute(request, uploadClient, MediaDto.serializer())
    }

    suspend fun createFeedbackJob(
        sessionId: String,
        request: FeedbackJobRequestDto,
        idempotencyKey: String,
    ): JobDto {
        val body = json.encodeToString(FeedbackJobRequestDto.serializer(), request)
        return postJson(
            path = "/v1/sessions/$sessionId/feedback-jobs",
            body = body,
            serializer = JobDto.serializer(),
            idempotencyKey = idempotencyKey,
        )
    }

    suspend fun getFeedback(feedbackId: String): FeedbackDto = getJson(
        path = "/v1/feedback/$feedbackId",
        serializer = FeedbackDto.serializer(),
    )

    suspend fun getEvidenceFrame(
        feedbackId: String,
        mediaId: String,
        frameIndex: Int,
        timestampS: Double,
    ): ByteArray? = withContext(Dispatchers.IO) {
        val path = "/v1/feedback/$feedbackId/evidence-frames/" +
            "$mediaId/$frameIndex?timestamp_s=$timestampS"
        val request = Request.Builder()
            .url("$baseUrl$path")
            .header("Accept", "image/jpeg")
            .get()
            .build()
        val response = try {
            client.newCall(request).execute()
        } catch (error: IOException) {
            throw NetworkException("无法连接本地服务，请检查服务端与 adb reverse。", error)
        }
        response.use {
            if (it.code == 404) return@use null
            if (!it.isSuccessful) {
                val text = it.body?.string().orEmpty()
                val detail = runCatching {
                    json.decodeFromString(ErrorEnvelopeDto.serializer(), text).error
                }.getOrNull()
                throw ApiException(
                    code = detail?.code ?: "HTTP_${it.code}",
                    message = detail?.message?.takeIf(String::isNotBlank)
                        ?: "证据帧请求失败（HTTP ${it.code}）。",
                    retryable = detail?.retryable ?: false,
                    requestId = detail?.requestId,
                    retryAfterS = detail?.retryAfterS,
                )
            }
            it.body?.bytes()
        }
    }

    suspend fun listFeedback(sessionId: String, stepId: String? = null): List<FeedbackDto> {
        val suffix = stepId?.let { "?step_id=$it" } ?: ""
        val response = getJson(
            path = "/v1/sessions/$sessionId/feedback$suffix",
            serializer = FeedbackListDto.serializer(),
        )
        return response.items
    }

    private suspend fun <T> getJson(
        path: String,
        serializer: DeserializationStrategy<T>,
        readClient: OkHttpClient = client,
    ): T = withContext(Dispatchers.IO) {
        val request = Request.Builder()
            .url("$baseUrl$path")
            .header("Accept", "application/json")
            .get()
            .build()
        execute(request, readClient, serializer)
    }

    private suspend fun <T> postJson(
        path: String,
        body: String,
        serializer: DeserializationStrategy<T>,
        idempotencyKey: String? = null,
        readClient: OkHttpClient = client,
    ): T = withContext(Dispatchers.IO) {
        val builder = Request.Builder()
            .url("$baseUrl$path")
            .header("Accept", "application/json")
            .post(body.toRequestBody(contentType))
        if (idempotencyKey != null) {
            builder.header("Idempotency-Key", idempotencyKey)
        }
        execute(builder.build(), readClient, serializer)
    }

    private suspend fun <T> patchJson(
        path: String,
        body: String,
        serializer: DeserializationStrategy<T>,
        idempotencyKey: String? = null,
        readClient: OkHttpClient = client,
    ): T = withContext(Dispatchers.IO) {
        val builder = Request.Builder()
            .url("$baseUrl$path")
            .header("Accept", "application/json")
            .patch(body.toRequestBody(contentType))
        if (idempotencyKey != null) {
            builder.header("Idempotency-Key", idempotencyKey)
        }
        execute(builder.build(), readClient, serializer)
    }

    private fun <T> execute(
        request: Request,
        readClient: OkHttpClient,
        serializer: DeserializationStrategy<T>,
    ): T {
        val response: Response = try {
            readClient.newCall(request).execute()
        } catch (error: IOException) {
            throw NetworkException("无法连接本地服务，请检查服务端与 adb reverse。", error)
        }
        return response.use {
            val text = it.body?.string().orEmpty()
            if (!it.isSuccessful) {
                val detail = runCatching {
                    json.decodeFromString(ErrorEnvelopeDto.serializer(), text).error
                }.getOrNull()
                throw ApiException(
                    code = detail?.code ?: "HTTP_${it.code}",
                    message = detail?.message?.takeIf(String::isNotBlank) ?: "请求失败（HTTP ${it.code}）。",
                    retryable = detail?.retryable ?: false,
                    requestId = detail?.requestId,
                    retryAfterS = detail?.retryAfterS,
                )
            }
            try {
                json.decodeFromString(serializer, text)
            } catch (error: Exception) {
                throw ApiException(
                    code = "MODEL_BAD_OUTPUT",
                    message = "服务端响应无法解析，请稍后重试。",
                    retryable = true,
                )
            }
        }
    }
}

private class ProgressRequestBody(
    private val file: File,
    private val mediaType: okhttp3.MediaType,
    private val onProgress: (Float) -> Unit,
) : okhttp3.RequestBody() {
    override fun contentType() = mediaType

    override fun contentLength(): Long = file.length()

    override fun writeTo(sink: BufferedSink) {
        val total = file.length().coerceAtLeast(1L)
        var written = 0L
        val buffer = ByteArray(DEFAULT_BUFFER_SIZE)
        file.inputStream().use { input ->
            while (true) {
                val read = input.read(buffer)
                if (read == -1) break
                sink.write(buffer, 0, read)
                written += read
                onProgress((written.toFloat() / total).coerceIn(0f, 1f))
            }
        }
    }
}
