package com.tutorialcoach.app.ui.screens.recipe

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.tutorialcoach.app.data.AdjustmentRequestDto
import com.tutorialcoach.app.data.ApiException
import com.tutorialcoach.app.data.RecipeGateway
import com.tutorialcoach.app.data.SessionActions
import com.tutorialcoach.app.data.TastingRequestDto
import com.tutorialcoach.app.data.WaterSourceConfirmationDto
import com.tutorialcoach.app.domain.DomainRecipe
import com.tutorialcoach.app.domain.DomainRecipeCompare
import com.tutorialcoach.app.domain.DomainRecipeVersion
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.booleanOrNull
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.doubleOrNull
import kotlinx.serialization.json.intOrNull
import kotlinx.serialization.json.jsonPrimitive

data class RecipeUiState(
    val loading: Boolean = false,
    val recipe: DomainRecipe? = null,
    val history: List<DomainRecipeVersion> = emptyList(),
    val comparison: DomainRecipeCompare? = null,
    val error: String? = null,
    val message: String? = null,
    val conflict: Boolean = false,
    val confirmation: WaterSourceConfirmationUi? = null,
)

data class WaterSourceCandidateUi(
    val candidateId: Int,
    val stepIndex: Int,
    val field: String,
    val label: String,
    val kind: String,
    val value: Double,
    val text: String,
    val roleHint: String,
) {
    fun displayText(): String = if (text.isNotBlank()) {
        "步骤 ${stepIndex + 1} · $text"
    } else {
        "步骤 ${stepIndex + 1} · " +
            (if (field == "target") "完成条件" else "执行步骤") +
            " · $label ${value}g"
    }
}

data class PendingAdjustment(
    val recipeId: String,
    val baseVersion: Int,
    val variable: String,
    val value: JsonElement,
    val reason: String,
)

data class WaterSourceConfirmationUi(
    val candidates: List<WaterSourceCandidateUi>,
    val pending: PendingAdjustment,
    val requiresFinal: Boolean = false,
    val declarationIds: Set<Int> = emptySet(),
    val finalIds: Set<Int> = emptySet(),
)

class RecipeViewModel(
    private val sessionActions: SessionActions,
    private val recipeGateway: RecipeGateway,
) : ViewModel() {
    private val _state = MutableStateFlow(RecipeUiState())
    val state: StateFlow<RecipeUiState> = _state.asStateFlow()

    init {
        refresh()
    }

    fun refresh() = loadRecipes(preserveAlerts = false)

    private fun loadRecipes(preserveAlerts: Boolean) {
        val session = sessionActions.session.value ?: return
        if (session.domain != "coffee") {
            _state.update { it.copy(error = "只有咖啡会话可以打开配方。", loading = false) }
            return
        }
        viewModelScope.launch {
            _state.update {
                if (preserveAlerts) it.copy(loading = true)
                else it.copy(loading = true, error = null, conflict = false)
            }
            try {
                val recipes = recipeGateway.listRecipes(session.id)
                val latest = recipes.maxByOrNull { it.version }
                val history = latest?.let { recipeGateway.listRecipeHistory(it.id) } ?: emptyList()
                _state.update {
                    it.copy(
                        loading = false,
                        recipe = latest,
                        history = history,
                        message = if (preserveAlerts) it.message else null,
                        error = if (preserveAlerts) it.error else null,
                        conflict = if (preserveAlerts) it.conflict else false,
                    )
                }
            } catch (error: Exception) {
                _state.update {
                    it.copy(loading = false, error = error.message ?: "配方加载失败。")
                }
            }
        }
    }

    fun createRecipe(useDemo: Boolean = false) {
        val session = sessionActions.session.value ?: return
        val planVersion = session.currentPlanVersion ?: run {
            _state.update { it.copy(error = "当前会话还没有计划，不能创建配方。") }
            return
        }
        viewModelScope.launch {
            _state.update { it.copy(loading = true, error = null) }
            try {
                val recipe = recipeGateway.createRecipe(session.id, planVersion, useDemo)
                val history = recipeGateway.listRecipeHistory(recipe.id)
                _state.update {
                    it.copy(
                        loading = false,
                        recipe = recipe,
                        history = history,
                        message = if (useDemo) {
                            "已创建 V60 演示配方 v${recipe.version}（15 g / 225 g / 92 °C / 150 秒）。"
                        } else {
                            "已按计划已确认参数创建配方 v${recipe.version}。"
                        },
                    )
                }
            } catch (error: Exception) {
                _state.update { it.copy(loading = false, error = error.message ?: "创建配方失败。") }
            }
        }
    }

    fun saveTasting(
        sourness: Int,
        sweetness: Int,
        bitterness: Int,
        body: Int,
        aroma: Int,
        aftertaste: Int,
        overall: Int,
        notes: String,
    ) {
        val recipe = _state.value.recipe ?: return
        viewModelScope.launch {
            _state.update { it.copy(loading = true, error = null) }
            try {
                recipeGateway.addTasting(
                    recipe.id,
                    TastingRequestDto(
                        sourness = sourness,
                        sweetness = sweetness,
                        bitterness = bitterness,
                        body = body,
                        aroma = aroma,
                        aftertaste = aftertaste,
                        overall = overall,
                        notes = notes,
                    ),
                )
                val history = recipeGateway.listRecipeHistory(recipe.id)
                _state.update {
                    it.copy(
                        loading = false,
                        history = history,
                        message = "口味记录已保存（仅用户输入）。",
                    )
                }
            } catch (error: Exception) {
                _state.update { it.copy(loading = false, error = error.message ?: "保存口味失败。") }
            }
        }
    }

    fun adjust(variable: String, valueText: String, reason: String) {
        val recipe = _state.value.recipe ?: return
        if (reason.isBlank()) {
            _state.update { it.copy(error = "请填写调整原因。") }
            return
        }
        val value = if (variable == "grind_setting") {
            JsonPrimitive(valueText.trim())
        } else {
            val numeric = valueText.trim().toDoubleOrNull()
            if (numeric == null || !numeric.isFinite()) {
                _state.update { it.copy(error = "新参数必须是有限数值。") }
                return
            }
            JsonPrimitive(numeric)
        }
        performAdjust(
            recipeId = recipe.id,
            baseVersion = recipe.version,
            variable = variable,
            value = value,
            reason = reason.trim(),
            confirmation = null,
        )
    }

    private fun performAdjust(
        recipeId: String,
        baseVersion: Int,
        variable: String,
        value: JsonElement,
        reason: String,
        confirmation: WaterSourceConfirmationDto?,
    ) {
        val pending = PendingAdjustment(recipeId, baseVersion, variable, value, reason)
        viewModelScope.launch {
            _state.update { it.copy(loading = true, error = null, conflict = false) }
            try {
                val (updated, _) = recipeGateway.adjustRecipe(
                    recipeId,
                    AdjustmentRequestDto(
                        baseVersion = baseVersion,
                        variable = variable,
                        toValue = value,
                        reason = reason,
                        waterSourceConfirmation = confirmation,
                    ),
                )
                val history = recipeGateway.listRecipeHistory(updated.id)
                _state.update {
                    it.copy(
                        loading = false,
                        recipe = updated,
                        history = history,
                        confirmation = null,
                        message = "已创建 v${updated.version}，只调整了 $variable。",
                    )
                }
            } catch (error: ApiException) {
                if (error.code == "VERSION_CONFLICT") {
                    _state.update {
                        it.copy(
                            loading = false,
                            conflict = true,
                            confirmation = null,
                            error = "配方版本已变化，已刷新最新版本；请重新调整。",
                        )
                    }
                    loadRecipes(preserveAlerts = true)
                } else {
                    val parsed = parseWaterConfirmation(error, pending)
                    if (parsed != null) {
                        _state.update {
                            it.copy(
                                loading = false,
                                confirmation = parsed,
                                error = "无法确认总水量来源，请选择总量声明与最终指令后重试。",
                            )
                        }
                    } else {
                        _state.update {
                            it.copy(loading = false, error = error.message)
                        }
                    }
                }
            } catch (error: Exception) {
                _state.update {
                    it.copy(loading = false, error = error.message ?: "调整失败。")
                }
            }
        }
    }

    private fun parseWaterConfirmation(
        error: ApiException,
        pending: PendingAdjustment,
    ): WaterSourceConfirmationUi? {
        val details = error.details
        if (details["reason"]?.jsonPrimitive?.contentOrNull != "total_source_unconfirmed") {
            return null
        }
        if (details["confirmation_required"]?.jsonPrimitive?.booleanOrNull != true) {
            return null
        }
        val array = details["candidates"] as? JsonArray ?: return null
        val requiresFinal =
            details["requires_final"]?.jsonPrimitive?.booleanOrNull == true
        val candidates = array.mapNotNull { element ->
            val item = element as? JsonObject ?: return@mapNotNull null
            WaterSourceCandidateUi(
                candidateId = item["candidate_id"]?.jsonPrimitive?.intOrNull
                    ?: return@mapNotNull null,
                stepIndex = item["step_index"]?.jsonPrimitive?.intOrNull ?: 0,
                field = item["field"]?.jsonPrimitive?.contentOrNull ?: "",
                label = item["label"]?.jsonPrimitive?.contentOrNull ?: "",
                kind = item["kind"]?.jsonPrimitive?.contentOrNull ?: "",
                value = item["value"]?.jsonPrimitive?.doubleOrNull ?: 0.0,
                text = item["text"]?.jsonPrimitive?.contentOrNull ?: "",
                roleHint = item["role_hint"]?.jsonPrimitive?.contentOrNull ?: "",
            )
        }
        if (candidates.isEmpty()) return null
        return WaterSourceConfirmationUi(
            candidates = candidates,
            pending = pending,
            requiresFinal = requiresFinal,
        )
    }

    fun toggleWaterDeclaration(candidateId: Int) {
        _state.update { current ->
            val confirmation = current.confirmation ?: return@update current
            current.copy(
                error = null,
                confirmation = confirmation.copy(
                    declarationIds = confirmation.declarationIds.toggle(candidateId),
                ),
            )
        }
    }

    fun toggleWaterFinal(candidateId: Int) {
        _state.update { current ->
            val confirmation = current.confirmation ?: return@update current
            current.copy(
                error = null,
                confirmation = confirmation.copy(
                    finalIds = confirmation.finalIds.toggle(candidateId),
                ),
            )
        }
    }

    fun confirmWaterSource() {
        val confirmation = _state.value.confirmation ?: return
        if (confirmation.declarationIds.isEmpty()) {
            _state.update { it.copy(error = "请选择总量声明来源。") }
            return
        }
        if (confirmation.requiresFinal && confirmation.finalIds.isEmpty()) {
            _state.update { it.copy(error = "请选择最终执行指令。") }
            return
        }
        val pending = confirmation.pending
        performAdjust(
            recipeId = pending.recipeId,
            baseVersion = pending.baseVersion,
            variable = pending.variable,
            value = pending.value,
            reason = pending.reason,
            confirmation = WaterSourceConfirmationDto(
                declaration = confirmation.declarationIds.sorted(),
                final = confirmation.finalIds.sorted(),
            ),
        )
    }

    fun cancelWaterSourceConfirmation() {
        _state.update { it.copy(confirmation = null, loading = false, error = null) }
    }

    private fun Set<Int>.toggle(candidateId: Int): Set<Int> =
        if (contains(candidateId)) this - candidateId else this + candidateId

    fun compareLatest() {
        val history = _state.value.history
        if (history.size < 2) {
            _state.update { it.copy(error = "至少需要两个版本才能对比。") }
            return
        }
        val base = history[history.size - 2]
        val target = history.last()
        viewModelScope.launch {
            _state.update { it.copy(loading = true, error = null) }
            try {
                val comparison = recipeGateway.compareRecipes(base.recipeId, target.recipeId)
                _state.update { it.copy(loading = false, comparison = comparison) }
            } catch (error: Exception) {
                _state.update { it.copy(loading = false, error = error.message ?: "对比失败。") }
            }
        }
    }

    fun dismissError() {
        _state.update { it.copy(error = null, conflict = false) }
    }
}
