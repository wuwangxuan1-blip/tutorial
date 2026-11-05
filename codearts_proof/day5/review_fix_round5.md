# D5 配方复审修复（2026-11-06，三项）

基线：`b47ba94`。只修以下三项，不进入 D6。

## 1. 步骤更新按变量语义，不再全局数字替换

- `RecipeService._rewrite_steps()` 改为按标签语义匹配：
  - 粉量：`咖啡粉/咖啡豆/粉量/粉重`；
  - 水量：`总注水/总水量/注水/水量`，或排除 `温杯用水/润洗用水/冲洗用水` 前后的独立“水”；
  - 水温：`水温/温度`；
  - 总时长：`总时长/总时间/时长/用时`；
  - 粉水比：`粉水比/比例`。
- 不再对所有数字字符串做全局替换，因此：
  - 咖啡粉 15→16 g 不会把“温杯用水 115 g”改成 116 g；
  - 不同变量恰好数值相同时，只更新对应语义标签下的值；
  - 旧版本仍保留原步骤文本。
- 回归 `test_semantic_step_rewrite_keeps_rinse_water_and_same_value_variables`：
  - 15→16 g 后新步骤为“咖啡粉 16 g，温杯用水 115 g”；
  - 新配方 dose=16、water=225、ratio=14.06、用料咖啡豆 16 g/水 225 g；
  - 旧 v1 仍为 15 g/225 g/温杯用水 115 g；
  - 直接测试“咖啡粉 15 g、水 15 g、水温 15 °C、总时长 15 秒”只改 dose 时，其余同值字段不变。

## 2. 中文冲煮总时长解析

- `_parse_brew_time()` 重写，按优先级支持：
  - `总时长约 3 分钟` → 180 秒；
  - `2 分 30 秒` → 150 秒；
  - `150 秒` → 150 秒；
  - 以及 `总时长 150 秒`、`约 2 分 30 秒` 等常见变体。
- 回归 `test_chinese_brew_time_variants` 直接断言 180/150/150。

## 3. 先校验输入，再派生粉水比

- 对唯一主动变量先做 `RecipeVariables` 类型/范围校验，再计算 `ratio = round(water/dose, 2)`。
- `dose_g=0`、非数字等非法值返回 **422 `INVALID_REQUEST`**（`reason=invalid_adjustment_value`），不会触发除零，也不会写入新版本。
- 正常水量调整与派生粉水比、单变量限制、版本冲突回归保留。
- 回归 `test_adjustment_validates_values_before_ratio_derivation`：
  - dose=0 → 422，版本列表仍为 [1]；
  - water_temp_c=`"abc"` → 422，旧版本 dose 仍 15；
  - 既有 225→240 派生 ratio=16、92→90、多变量拒绝、版本冲突、失败不写入均通过。

## 本轮实测

- 服务端：`.venv/Scripts/python.exe -m pytest -o addopts=""` → **114 passed / 0 failed**（配方测试由 5 增至 8）。
- Android：`:app:testDebugUnitTest --rerun-tasks` → **55 tests / 0 failures**（本轮未改 Android）。
- `:app:assembleDebug` → BUILD SUCCESSFUL；APK **10,822,322 字节**。
- 真实模型 V60 重跑（计划解析路径）：15/225/15/92/150 → 品尝 → water_temp_c 90 → v2；compare `92→90, delta -2`。

## 状态分列

- **第三方实拍链路：通过**（照片/短片 `unclear`；倒咖啡反例 `not_met`；证据帧 9/9 字节一致）。
- **用户自拍环绕验收：BLOCKED**（无用户自拍环绕素材）。
- **真机配方对比：BLOCKED**（真机 v1 与用户评分已保存；92→90/对比未完成）。
- **真机断网重试：BLOCKED**（未取得错误→恢复→重试成功证据）。
- 真机 Canvas easing/拖动：未复测，由 JVM 覆盖。
- 未调整提示词；不进入 D6。