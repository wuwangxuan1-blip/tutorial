package com.tutorialcoach.app.data

import java.io.IOException
import java.util.UUID
import java.util.concurrent.TimeUnit
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response

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

    private suspend fun <T> getJson(
        path: String,
        serializer: kotlinx.serialization.DeserializationStrategy<T>,
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
        serializer: kotlinx.serialization.DeserializationStrategy<T>,
        idempotencyKey: String? = null,
    ): T = withContext(Dispatchers.IO) {
        val builder = Request.Builder()
            .url("$baseUrl$path")
            .header("Accept", "application/json")
            .post(body.toRequestBody(contentType))
        if (idempotencyKey != null) {
            builder.header("Idempotency-Key", idempotencyKey)
        }
        execute(builder.build(), client, serializer)
    }

    private fun <T> execute(
        request: Request,
        readClient: OkHttpClient,
        serializer: kotlinx.serialization.DeserializationStrategy<T>,
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