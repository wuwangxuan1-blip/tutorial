package com.tutorialcoach.app.ui.screens.recipe

import com.tutorialcoach.app.data.AdjustmentRequestDto
import com.tutorialcoach.app.data.ApiException
import com.tutorialcoach.app.data.JobDto
import com.tutorialcoach.app.data.RecipeGateway
import com.tutorialcoach.app.data.SessionActions
import com.tutorialcoach.app.data.TastingRequestDto
import com.tutorialcoach.app.domain.DomainAdjustment
import com.tutorialcoach.app.domain.DomainAnswer
import com.tutorialcoach.app.domain.DomainImpact
import com.tutorialcoach.app.domain.DomainPlan
import com.tutorialcoach.app.domain.DomainProgress
import com.tutorialcoach.app.domain.DomainRecipe
import com.tutorialcoach.app.domain.DomainRecipeCompare
import com.tutorialcoach.app.domain.DomainRecipeIngredient
import com.tutorialcoach.app.domain.DomainRecipeStep
import com.tutorialcoach.app.domain.DomainRecipeVariables
import com.tutorialcoach.app.domain.DomainRecipeVersion
import com.tutorialcoach.app.domain.DomainRevision
import com.tutorialcoach.app.domain.DomainSession
import com.tutorialcoach.app.domain.DomainTasting
import com.tutorialcoach.app.domain.DomainVariableDiff
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import kotlinx.serialization.json.addJsonObject
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put
import kotlinx.serialization.json.putJsonArray
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class RecipeViewModelTest {
    private val dispatcher = StandardTestDispatcher()

    @Before
    fun setUp() {
        Dispatchers.setMain(dispatcher)
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    private fun variables(temp: Double = 92.0) = DomainRecipeVariables(
        doseG = 15.0,
        waterG = 225.0,
        ratio = 15.0,
        waterTempC = temp,
        grindSetting = "中细",
        brewTimeS = 150,
    )

    private fun recipe(version: Int = 1, temp: Double = 92.0) = DomainRecipe(
        id = "recipe_v$version",
        sessionId = "sess_1",
        version = version,
        name = "V60 手冲",
        brewer = "V60",
        method = "pour_over",
        servings = 1,
        variables = variables(temp),
        ingredients = listOf(DomainRecipeIngredient("咖啡豆", 15.0, "g")),
        steps = listOf(DomainRecipeStep("rst_1", 1, "闷蒸 30 秒", 30, "粉层湿润")),
        sourcePlanVersion = 1,
        createdAt = "2026-11-05T00:00:00Z",
    )

    private fun tasting(version: Int) = DomainTasting(
        id = "taste_$version",
        recipeId = "recipe_v$version",
        recipeVersion = version,
        sourness = 3,
        sweetness = 3,
        bitterness = 3,
        body = 3,
        aroma = 3,
        aftertaste = 3,
        overall = 3,
        notes = "用户输入",
        createdAt = "2026-11-05T00:00:00Z",
    )

    private inner class FakeSessions : SessionActions {
        override val session: StateFlow<DomainSession?> = MutableStateFlow(
            DomainSession(
                id = "sess_1",
                domain = "coffee",
                goal = "V60 手冲",
                status = "in_progress",
                questions = emptyList(),
                currentPlanVersion = 1,
            ),
        )
        override val plan: StateFlow<DomainPlan?> = MutableStateFlow(null)
        override val progress: StateFlow<DomainProgress> = MutableStateFlow(DomainProgress())

        override suspend fun loadPlan(sessionId: String): DomainPlan = throw UnsupportedOperationException()
        override suspend fun updateProgress(sessionId: String, update: com.tutorialcoach.app.data.ProgressUpdate): DomainProgress =
            throw UnsupportedOperationException()
        override suspend fun pauseSession(sessionId: String): DomainSession = throw UnsupportedOperationException()
        override suspend fun resumeSession(sessionId: String): DomainSession = throw UnsupportedOperationException()
        override suspend fun completeSession(sessionId: String, rating: Int?, notes: String): DomainSession =
            throw UnsupportedOperationException()
        override suspend fun ask(sessionId: String, question: String, stepId: String, planVersion: Int): DomainAnswer =
            throw UnsupportedOperationException()
        override suspend fun patchConditions(
            sessionId: String,
            basePlanVersion: Int?,
            conditions: Map<String, kotlinx.serialization.json.JsonElement?>,
        ): DomainImpact = throw UnsupportedOperationException()
        override suspend fun createRevisionJob(
            sessionId: String,
            basePlanVersion: Int,
            requestReason: String,
            idempotencyKey: String,
        ): JobDto = throw UnsupportedOperationException()
        override suspend fun getJob(jobId: String): JobDto = throw UnsupportedOperationException()
        override suspend fun listRevisions(sessionId: String): List<DomainRevision> = emptyList()
        override suspend fun applyRevision(sessionId: String, revisionId: String, basePlanVersion: Int): DomainPlan =
            throw UnsupportedOperationException()
        override suspend fun rejectRevision(sessionId: String, revisionId: String, reason: String): DomainRevision =
            throw UnsupportedOperationException()
    }

    private inner class FakeGateway : RecipeGateway {
        var recipes = mutableListOf<DomainRecipe>()
        var history = mutableListOf<DomainRecipeVersion>()
        var conflict = false
        var lastAdjustment: AdjustmentRequestDto? = null
        var lastTasting: TastingRequestDto? = null
        var comparison: DomainRecipeCompare? = null
        var lastDemo = false
        var confirmationRequired = false
        var conflictOnConfirmation = false
        val requests = mutableListOf<AdjustmentRequestDto>()

        override suspend fun createRecipe(
            sessionId: String,
            basePlanVersion: Int,
            demo: Boolean,
        ): DomainRecipe {
            lastDemo = demo
            val created = recipe()
            recipes = mutableListOf(created)
            history = mutableListOf(
                DomainRecipeVersion(created.id, 1, created.name, created.variables, created.createdAt, null, null),
            )
            return created
        }

        override suspend fun listRecipes(sessionId: String): List<DomainRecipe> = recipes
        override suspend fun getRecipe(recipeId: String): DomainRecipe = recipes.last()

        override suspend fun addTasting(
            recipeId: String,
            request: TastingRequestDto,
        ): DomainTasting {
            lastTasting = request
            val item = tasting(1)
            history[0] = history[0].copy(tasting = item)
            return item
        }

        override suspend fun adjustRecipe(
            recipeId: String,
            request: AdjustmentRequestDto,
        ): Pair<DomainRecipe, DomainAdjustment> {
            lastAdjustment = request
            requests.add(request)
            if (conflict) throw ApiException("VERSION_CONFLICT", "配方版本已变化。")
            if (conflictOnConfirmation && request.waterSourceConfirmation != null) {
                throw ApiException("VERSION_CONFLICT", "配方版本已变化。")
            }
            if (confirmationRequired && request.waterSourceConfirmation == null) {
                throw ApiException(
                    "INVALID_REQUEST",
                    "无法确认旧配方的总水量来源。",
                    details = buildJsonObject {
                        put("reason", "total_source_unconfirmed")
                        put("confirmation_required", true)
                        put("confirm_field", "water_source_confirmation")
                        putJsonArray("candidates") {
                            addJsonObject {
                                put("candidate_id", 0)
                                put("step_index", 0)
                                put("field", "instruction")
                                put("label", "总水量")
                                put("kind", "explicit")
                                put("value", 225.0)
                                put("role_hint", "declaration")
                            }
                            addJsonObject {
                                put("candidate_id", 1)
                                put("step_index", 0)
                                put("field", "target")
                                put("label", "注水至")
                                put("kind", "terminal")
                                put("value", 225.0)
                                put("role_hint", "final_or_mid")
                            }
                        }
                    },
                )
            }
            val updated = recipe(2, 94.0)
            recipes.add(updated)
            history.add(
                DomainRecipeVersion(updated.id, 2, updated.name, updated.variables, updated.createdAt, null, null),
            )
            val adjustment = DomainAdjustment(
                id = "adj_1",
                recipeId = recipeId,
                baseVersion = 1,
                newVersion = 2,
                variable = request.variable,
                fromValue = "92.0",
                toValue = "94.0",
                reason = request.reason,
                expectedEffect = "仅调整水温。",
                tastingId = null,
                createdAt = "2026-11-05T00:00:00Z",
            )
            return updated to adjustment
        }

        override suspend fun listRecipeHistory(recipeId: String): List<DomainRecipeVersion> = history

        override suspend fun compareRecipes(recipeId: String, againstId: String): DomainRecipeCompare =
            comparison ?: DomainRecipeCompare(
                baseRecipeId = recipeId,
                baseVersion = 1,
                targetRecipeId = againstId,
                targetVersion = 2,
                variableDiffs = listOf(DomainVariableDiff("water_temp_c", "92.0", "94.0", 2.0)),
                tastingDeltas = mapOf("overall" to 1),
                notes = listOf("只比较用户主观评分与参数，不代表客观质量结论。"),
            )
    }

    @Test
    fun createTastingAdjustAndCompareFlow() = runTest(dispatcher) {
        val gateway = FakeGateway()
        val viewModel = RecipeViewModel(FakeSessions(), gateway)
        advanceUntilIdle()
        viewModel.createRecipe()
        advanceUntilIdle()
        assertEquals(1, viewModel.state.value.recipe?.version)

        viewModel.saveTasting(3, 3, 3, 3, 3, 3, 3, "入口偏酸")
        advanceUntilIdle()
        assertNotNull(viewModel.state.value.history.firstOrNull()?.tasting)

        viewModel.adjust("water_temp_c", "94", "只改水温")
        advanceUntilIdle()
        assertEquals(2, viewModel.state.value.recipe?.version)
        assertEquals("water_temp_c", gateway.lastAdjustment?.variable)
        assertEquals(1, gateway.lastAdjustment?.baseVersion)

        viewModel.compareLatest()
        advanceUntilIdle()
        assertEquals("water_temp_c", viewModel.state.value.comparison?.variableDiffs?.first()?.variable)
    }

    @Test
    fun versionConflictRefreshesWithoutOverwritingLatestRecipe() = runTest(dispatcher) {
        val gateway = FakeGateway()
        gateway.recipes = mutableListOf(recipe(2))
        gateway.history = mutableListOf(
            DomainRecipeVersion("recipe_v1", 1, "V60", variables(), "", null, null),
            DomainRecipeVersion("recipe_v2", 2, "V60", variables(94.0), "", null, null),
        )
        gateway.conflict = true
        val viewModel = RecipeViewModel(FakeSessions(), gateway)
        advanceUntilIdle()
        viewModel.adjust("water_temp_c", "95", "旧版本调整")
        advanceUntilIdle()

        assertTrue(viewModel.state.value.conflict)
        assertEquals(2, viewModel.state.value.recipe?.version)
        assertTrue(viewModel.state.value.error?.contains("已刷新") == true)
    }

    @Test
    fun invalidNumericValueDoesNotCallGateway() = runTest(dispatcher) {
        val gateway = FakeGateway()
        gateway.recipes = mutableListOf(recipe())
        val viewModel = RecipeViewModel(FakeSessions(), gateway)
        advanceUntilIdle()
        viewModel.adjust("water_temp_c", "abc", "测试")
        advanceUntilIdle()
        assertEquals(null, gateway.lastAdjustment)
        assertTrue(viewModel.state.value.error?.contains("有限数值") == true)
    }

    @Test
    fun demoSelectionIsForwardedToGateway() = runTest(dispatcher) {
        val gateway = FakeGateway()
        val viewModel = RecipeViewModel(FakeSessions(), gateway)
        advanceUntilIdle()
        viewModel.createRecipe(useDemo = true)
        advanceUntilIdle()
        assertTrue(gateway.lastDemo)
        assertEquals(1, viewModel.state.value.recipe?.version)
    }

    @Test
    fun waterSourceConfirmationShowsCandidatesAndRetriesWithSameBaseVersion() =
        runTest(dispatcher) {
            val gateway = FakeGateway()
            gateway.recipes = mutableListOf(recipe())
            gateway.confirmationRequired = true
            val viewModel = RecipeViewModel(FakeSessions(), gateway)
            advanceUntilIdle()

            viewModel.adjust("water_g", "240", "调整总水量")
            advanceUntilIdle()

            val confirmation = viewModel.state.value.confirmation
            assertNotNull(confirmation)
            assertEquals(2, confirmation!!.candidates.size)
            assertTrue(confirmation.candidates.first().displayText().contains("总水量"))

            viewModel.toggleWaterDeclaration(0)
            viewModel.toggleWaterFinal(1)
            viewModel.confirmWaterSource()
            advanceUntilIdle()

            assertEquals(2, viewModel.state.value.recipe?.version)
            assertEquals(2, gateway.requests.size)
            val last = gateway.requests.last()
            assertEquals(1, last.baseVersion)
            assertEquals("water_g", last.variable)
            assertEquals("调整总水量", last.reason)
            assertEquals(listOf(0), last.waterSourceConfirmation?.declaration)
            assertEquals(listOf(1), last.waterSourceConfirmation?.final)
        }

    @Test
    fun cancelWaterSourceConfirmationDoesNotRetry() = runTest(dispatcher) {
        val gateway = FakeGateway()
        gateway.recipes = mutableListOf(recipe())
        gateway.confirmationRequired = true
        val viewModel = RecipeViewModel(FakeSessions(), gateway)
        advanceUntilIdle()

        viewModel.adjust("water_g", "240", "调整总水量")
        advanceUntilIdle()
        assertNotNull(viewModel.state.value.confirmation)

        viewModel.cancelWaterSourceConfirmation()
        advanceUntilIdle()

        assertEquals(null, viewModel.state.value.confirmation)
        assertEquals(1, gateway.requests.size)
        assertEquals(1, viewModel.state.value.recipe?.version)
    }

    @Test
    fun confirmationRetryVersionConflictSurfacesConflict() = runTest(dispatcher) {
        val gateway = FakeGateway()
        gateway.recipes = mutableListOf(recipe())
        gateway.confirmationRequired = true
        gateway.conflictOnConfirmation = true
        val viewModel = RecipeViewModel(FakeSessions(), gateway)
        advanceUntilIdle()

        viewModel.adjust("water_g", "240", "调整总水量")
        advanceUntilIdle()
        viewModel.toggleWaterDeclaration(0)
        viewModel.confirmWaterSource()
        advanceUntilIdle()

        assertTrue(viewModel.state.value.conflict)
        assertEquals(null, viewModel.state.value.confirmation)
        assertTrue(viewModel.state.value.error?.contains("已刷新") == true)
        assertEquals(2, gateway.requests.size)
    }
}