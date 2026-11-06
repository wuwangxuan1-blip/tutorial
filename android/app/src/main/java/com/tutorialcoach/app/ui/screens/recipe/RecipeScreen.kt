package com.tutorialcoach.app.ui.screens.recipe

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.layout.width
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.Checkbox
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FilterChip
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
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.Alignment
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.lifecycle.viewmodel.initializer
import androidx.lifecycle.viewmodel.viewModelFactory
import com.tutorialcoach.app.di.AppContainer
import com.tutorialcoach.app.domain.DomainRecipe
import com.tutorialcoach.app.domain.DomainRecipeCompare
import com.tutorialcoach.app.domain.DomainRecipeVariables
import com.tutorialcoach.app.ui.components.ErrorBanner

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RecipeScreen(
    container: AppContainer,
    onBack: () -> Unit,
) {
    val session by container.repository.session.collectAsStateWithLifecycle()
    val viewModel: RecipeViewModel = viewModel(
        key = session?.id ?: "no-session",
        factory = viewModelFactory {
            initializer { RecipeViewModel(container.repository, container.repository) }
        },
    )
    val state by viewModel.state.collectAsStateWithLifecycle()
    var useDemo by remember { mutableStateOf(false) }

    state.confirmation?.let { confirmation ->
        WaterSourceConfirmationDialog(
            confirmation = confirmation,
            onToggleDeclaration = viewModel::toggleWaterDeclaration,
            onToggleFinal = viewModel::toggleWaterFinal,
            onConfirm = viewModel::confirmWaterSource,
            onCancel = viewModel::cancelWaterSourceConfirmation,
        )
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("咖啡配方") },
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
            Text(
                "默认从当前计划读取你已确认的粉量、水量、水温和时长创建配方。V60 演示参数（15 g / 225 g / 92 °C / 150 秒）只在明确勾选后使用。口味评分与描述只能由你填写。",
                style = MaterialTheme.typography.bodyMedium,
            )
            Text(
                "设备缺失时：无磨豆机可用店家代磨；无电子秤可用量杯/量勺估算；服务端不会编造设备型号或精确参数。",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            if (state.loading) {
                LinearProgressIndicator(modifier = Modifier.fillMaxWidth())
            }
            state.error?.let {
                ErrorBanner(
                    message = it,
                    retryable = false,
                    onRetry = null,
                    onDismiss = viewModel::dismissError,
                )
            }
            state.message?.let {
                Text(it, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.primary)
            }

            val recipe = state.recipe
            if (recipe == null) {
                Card(modifier = Modifier.fillMaxWidth()) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(10.dp),
                    ) {
                        Text("还没有配方", style = MaterialTheme.typography.titleMedium)
                        Text(
                            "从当前咖啡计划创建 v1 后，可记录用户口味、单变量调整并对比历史版本。",
                            style = MaterialTheme.typography.bodyMedium,
                        )
                        FilterChip(
                            selected = useDemo,
                            onClick = { useDemo = !useDemo },
                            label = { Text("明确使用 V60 演示参数（15/225/92/150）") },
                        )
                        Button(
                            onClick = { viewModel.createRecipe(useDemo) },
                            enabled = !state.loading && session?.domain == "coffee",
                            modifier = Modifier.fillMaxWidth(),
                        ) {
                            Text(if (useDemo) "创建 V60 演示配方" else "按计划参数创建配方")
                        }
                    }
                }
                return@Column
            }

            RecipeHeader(recipe)
            RecipeVariablesCard(recipe.variables)
            RecipeStepsCard(recipe)
            TastingCard(recipe.id, viewModel, state.loading)
            AdjustmentCard(recipe, viewModel, state.loading)
            HistoryCard(state.history, viewModel)
            state.comparison?.let { compare -> CompareCard(compare) }
        }
    }
}

@Composable
private fun RecipeHeader(recipe: DomainRecipe) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(4.dp),
        ) {
            Text(recipe.name, style = MaterialTheme.typography.titleLarge)
            Text(
                "v${recipe.version} · ${recipe.brewer} · ${recipe.method} · ${recipe.servings} 份",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun RecipeVariablesCard(variables: DomainRecipeVariables) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            Text("参数", style = MaterialTheme.typography.titleMedium)
            variables.entries().forEach { (label, value) ->
                Text("$label：$value", style = MaterialTheme.typography.bodyMedium)
            }
        }
    }
}

@Composable
private fun RecipeStepsCard(recipe: DomainRecipe) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text("步骤 / 时间轴", style = MaterialTheme.typography.titleMedium)
            recipe.steps.forEach { step ->
                Text(
                    "${step.order}. ${step.instruction}（${step.durationS} 秒）",
                    style = MaterialTheme.typography.bodyMedium,
                )
                Text(
                    "目标：${step.target}",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}

@Composable
private fun TastingCard(
    recipeId: String,
    viewModel: RecipeViewModel,
    loading: Boolean,
) {
    var sourness by remember(recipeId) { mutableStateOf(3) }
    var sweetness by remember(recipeId) { mutableStateOf(3) }
    var bitterness by remember(recipeId) { mutableStateOf(3) }
    var body by remember(recipeId) { mutableStateOf(3) }
    var aroma by remember(recipeId) { mutableStateOf(3) }
    var aftertaste by remember(recipeId) { mutableStateOf(3) }
    var overall by remember(recipeId) { mutableStateOf(3) }
    var notes by remember(recipeId) { mutableStateOf("") }

    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text("记录品尝（用户输入）", style = MaterialTheme.typography.titleMedium)
            Text(
                "模型不会从照片推断口味或萃取结果。",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                ScoreField("酸", sourness) { sourness = it }
                ScoreField("甜", sweetness) { sweetness = it }
                ScoreField("苦", bitterness) { bitterness = it }
            }
            Row(horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                ScoreField("醇厚", body) { body = it }
                ScoreField("香气", aroma) { aroma = it }
                ScoreField("余韵", aftertaste) { aftertaste = it }
            }
            ScoreField("总体", overall) { overall = it }
            OutlinedTextField(
                value = notes,
                onValueChange = { if (it.length <= 500) notes = it },
                label = { Text("口味描述（≤500 字）") },
                modifier = Modifier.fillMaxWidth(),
                minLines = 2,
            )
            Button(
                onClick = {
                    viewModel.saveTasting(
                        sourness, sweetness, bitterness, body, aroma, aftertaste, overall, notes,
                    )
                },
                enabled = !loading,
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text("保存口味记录")
            }
        }
    }
}

@Composable
private fun AdjustmentCard(
    recipe: DomainRecipe,
    viewModel: RecipeViewModel,
    loading: Boolean,
) {
    val options = variableOptions(recipe.variables)
    var selected by remember(recipe.id, options) {
        mutableStateOf(
            options.firstOrNull { it.first == "water_temp_c" }?.first
                ?: options.firstOrNull()?.first
                ?: "",
        )
    }
    var valueText by remember(recipe.id, selected) {
        mutableStateOf(options.firstOrNull { it.first == selected }?.second ?: "")
    }
    var reason by remember(recipe.id) { mutableStateOf("") }

    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text("单变量调整", style = MaterialTheme.typography.titleMedium)
            Text(
                "每次只改一个变量；成功后才创建新版本，旧版本只读。",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
            options.forEach { (name, current) ->
                FilterChip(
                    selected = selected == name,
                    onClick = {
                        selected = name
                        valueText = current
                    },
                    label = { Text("$name = $current") },
                )
            }
            Text("新值：$valueText", style = MaterialTheme.typography.bodySmall)
            OutlinedTextField(
                value = valueText,
                onValueChange = { valueText = it },
                label = { Text("新参数值（只改 $selected）") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
            )
            OutlinedTextField(
                value = reason,
                onValueChange = { if (it.length <= 300) reason = it },
                label = { Text("调整原因（≤300 字）") },
                modifier = Modifier.fillMaxWidth(),
                minLines = 2,
            )
            Button(
                onClick = { viewModel.adjust(selected, valueText, reason) },
                enabled = !loading && selected.isNotBlank(),
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text("创建新版本（单变量）")
            }
        }
    }
}

@Composable
private fun WaterSourceConfirmationDialog(
    confirmation: WaterSourceConfirmationUi,
    onToggleDeclaration: (Int) -> Unit,
    onToggleFinal: (Int) -> Unit,
    onConfirm: () -> Unit,
    onCancel: () -> Unit,
) {
    AlertDialog(
        onDismissRequest = onCancel,
        title = { Text("确认总水量来源") },
        text = {
            Column(
                modifier = Modifier.verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                Text("请选择总量声明与最终执行指令。中途注水不会被改动。")
                confirmation.candidates.forEach { candidate ->
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Checkbox(
                            checked = candidate.candidateId in confirmation.declarationIds,
                            onCheckedChange = { onToggleDeclaration(candidate.candidateId) },
                        )
                        Text("总量", style = MaterialTheme.typography.labelSmall)
                        Checkbox(
                            checked = candidate.candidateId in confirmation.finalIds,
                            onCheckedChange = { onToggleFinal(candidate.candidateId) },
                        )
                        Text("最终", style = MaterialTheme.typography.labelSmall)
                        Text(
                            candidate.displayText(),
                            modifier = Modifier.weight(1f),
                            style = MaterialTheme.typography.bodySmall,
                        )
                    }
                }
            }
        },
        confirmButton = {
            TextButton(onClick = onConfirm) { Text("确认并重试") }
        },
        dismissButton = {
            TextButton(onClick = onCancel) { Text("取消") }
        },
    )
}

@Composable
private fun HistoryCard(
    history: List<com.tutorialcoach.app.domain.DomainRecipeVersion>,
    viewModel: RecipeViewModel,
) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text("版本历史", style = MaterialTheme.typography.titleMedium)
            history.forEach { version ->
                Text(
                    "v${version.version} · ${version.variables.entries().joinToString(" · ") { "${it.first}=${it.second}" }}",
                    style = MaterialTheme.typography.bodyMedium,
                )
                version.tasting?.let {
                    Text(
                        "用户评分：酸 ${it.sourness} / 甜 ${it.sweetness} / 苦 ${it.bitterness} / 总体 ${it.overall}",
                        style = MaterialTheme.typography.bodySmall,
                    )
                }
            }
            if (history.size >= 2) {
                OutlinedButton(
                    onClick = viewModel::compareLatest,
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Text("对比最近两个版本")
                }
            }
        }
    }
}

@Composable
private fun CompareCard(comparison: DomainRecipeCompare) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(6.dp),
        ) {
            Text(
                "对比 v${comparison.baseVersion} → v${comparison.targetVersion}",
                style = MaterialTheme.typography.titleMedium,
            )
            comparison.variableDiffs.forEach { diff ->
                Text(
                    "${diff.variable}：${diff.baseValue} → ${diff.targetValue}" +
                        (diff.delta?.let { "（Δ${it}）" } ?: ""),
                    style = MaterialTheme.typography.bodyMedium,
                )
            }
            comparison.tastingDeltas?.let { deltas ->
                Text(
                    "用户评分差异：" + deltas.entries.joinToString(" · ") { "${it.key} ${it.value}" },
                    style = MaterialTheme.typography.bodySmall,
                )
            }
            comparison.notes.forEach {
                Text(
                    "• $it",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
    }
}

@Composable
private fun ScoreField(label: String, value: Int, onChange: (Int) -> Unit) {
    OutlinedTextField(
        value = value.toString(),
        onValueChange = { text -> text.toIntOrNull()?.let { onChange(it.coerceIn(1, 5)) } },
        label = { Text(label) },
        modifier = Modifier.width(72.dp),
        singleLine = true,
    )
}

private fun variableOptions(variables: DomainRecipeVariables): List<Pair<String, String>> = listOfNotNull(
    variables.doseG?.let { "dose_g" to it.toString() },
    variables.waterG?.let { "water_g" to it.toString() },

    variables.waterTempC?.let { "water_temp_c" to it.toString() },
    variables.grindSetting?.let { "grind_setting" to it },
    variables.brewTimeS?.let { "brew_time_s" to it.toString() },
    variables.milkMl?.let { "milk_ml" to it.toString() },
    variables.iceG?.let { "ice_g" to it.toString() },
    variables.sweetenerG?.let { "sweetener_g" to it.toString() },
)
