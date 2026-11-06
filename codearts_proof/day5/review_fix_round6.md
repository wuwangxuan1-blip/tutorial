# D5 配方复审修复（2026-11-06，两项）

基线：`1376a51`。只修以下两项，不进入 D6。

## 1. 创建配方区分闷蒸/分段注水与总水量

- 新增 `_parse_water_total()`：
  - 优先识别总量标识：`总注水/总水量/累计注水/最终注水/总计/合计/继续注水至/继续注水到/注水至/注水到/加水至/加到`。
  - 只有单一未歧义水量时才采用普通 `水/注水/水量`。
  - 出现多个未标总量的注水量时返回 **422 `INVALID_REQUEST`**（`reason=water_total_ambiguous`），列出候选值，不创建配方、不猜测总量。
- 回归 `test_recipe_water_total_uses_cumulative_water_and_rejects_ambiguous`：
  - “咖啡粉 15 g，闷蒸注水 30 g，继续注水至 225 g，水温 92 °C，总时长 150 秒” → **water_g=225、ratio=15.0**，用料水 225 g；
  - “咖啡粉 15 g，闷蒸注水 30 g，再注水 90 g……” → 422 `water_total_ambiguous`，会话无配方。

## 2. 显式总时长优先，并改写中文分钟时长步骤

- `_parse_brew_time()` 优先匹配 `总时长/总时间`，再匹配单步 `时长/用时`：
  - `用时 30 秒。总时长 150 秒` → **150 秒**；
  - `总时长 2 分 30 秒` → **150 秒**；
  - 保留 `约 3 分钟`→180 秒、`2 分 30 秒`→150 秒、`150 秒`→150 秒。
- `_rewrite_steps()` 的总时长操作改为识别中文分钟表达（如 `总时长 2 分 30 秒`、`总时长 3 分钟`）与秒表达；150→180 秒后步骤规范化为 **“总时长 180 秒”**，不依赖全局数字替换，也不改单步“闷蒸 30 秒”。
- 回归 `test_recipe_explicit_total_time_wins_and_adjustment_rewrites_chinese_duration`：
  - 创建时取总时长 150 秒；
  - 调整 `brew_time_s=180` 后新版参数 180、步骤含“总时长 180 秒”、不含“2 分 30 秒”；
  - 旧版仍为 150 秒且保留“2 分 30 秒”。

## 本轮实测

- 服务端：`.venv/Scripts/python.exe -m pytest -o addopts=""` → **116 passed / 0 failed**（配方测试由 8 增至 10）。
- Android：`:app:testDebugUnitTest --rerun-tasks` → **55 tests / 0 failures**（本轮未改 Android）。
- `:app:assembleDebug` → BUILD SUCCESSFUL；APK **10,822,322 字节**。
- 真实模型 V60 重跑：计划解析总水量 225、粉水比 1:15；92→90 v2/compare 通过。
- 保留上轮语义步骤、同值变量、中文时长、先校验后派生、水量派生、单变量与版本冲突回归。

## 状态分列

- **第三方实拍链路：通过**（照片/短片 `unclear`；倒咖啡反例 `not_met`；证据帧 9/9 字节一致）。
- **用户自拍环绕验收：BLOCKED**（无用户自拍环绕素材）。
- **真机配方对比：BLOCKED**（真机 v1 与用户评分已保存；92→90/对比未完成）。
- **真机断网重试：BLOCKED**（未取得错误→恢复→重试成功证据）。
- 真机 Canvas easing/拖动：未复测，由 JVM 覆盖。
- 未调整提示词；不进入 D6。