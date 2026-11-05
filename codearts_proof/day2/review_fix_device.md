# P2/P3 复审修复与真机复核（2026-11-05）

基线：`a486b65`。本文件只记录 P2（过敏提示槽位）与 P3（共享限流冷却）两项修复，不涉及 P2/D3。

## 1. 实现要点

### P2 过敏提示预留槽位

- `server/app/services/plan_service.py` 对模型假设去重并保持原顺序。
- 用户未提供过敏信息（`allergies` 为 `None`）时，为通用提示预留 1 个槽位：模型假设最多保留前 9 条，第 10 条固定为
  “未提供过敏信息，请核对本次实际使用的食材和调味料；无法确认是否存在过敏原。”
- `allergies=[]`（明确无过敏）不添加该提示；模型已自行返回同一提示时不重复追加。
- 最终 `assumptions` 始终 ≤10 条，满足 `PlanOut.assumptions` 的 `max_length=10`。

### P3 应用级共享限流冷却

- 新增 `android/.../data/RateLimitGate.kt`，由 `AppContainer` 持有；冷却状态不再存放在 `PlanViewModel` 内。
- `PlanScreen` 按 session id 创建 ViewModel 时传入同一个 `container.rateLimitGate`，切换会话不会丢失剩余冷却。
- 冷却期间 `generate()` 与 `retry()` 都在 ViewModel 层拦截，不会调用 `createPlanJob`；页面生成按钮禁用，错误区重试按钮隐藏。
- 切换会话只取消旧轮询、清理旧页面状态，并把新会话恢复为 Ready/Idle；旧错误不会覆盖新会话。
- 倒计时按秒递减，结束后恢复手动生成/重试。

## 2. 测试与构建（本轮实测）

- 服务端：`.venv/Scripts/python.exe -m pytest -o addopts=""` → **48 passed**，0 失败。
  - `test_contract_examples` 8、`test_health` 3、`test_idempotency` 5、`test_model_client_errors` 8、`test_plan_assumptions` 3、`test_plan_flow` 6、`test_plan_repair` 6、`test_sessions` 9。
  - 新增 `test_allergy_note_reserves_slot_when_model_returns_ten`：10 条模型假设 + 未填过敏 → 恰好 10 条，前 9 条保持模型顺序，通用提示第 10 条且恰好一次。
  - 保留 `test_allergy_assumption_is_generic_for_mushroom_soup` 与 `test_explicit_no_allergies_skips_generic_allergy_note`。
- 安卓：`gradlew.bat --no-daemon --rerun-tasks :app:testDebugUnitTest :app:assembleDebug` → **BUILD SUCCESSFUL**。
  - JVM 测试 **21 项，0 失败**：`ContractExamplesTest` 6、`DtoTest` 3、`ErrorMapperTest` 5、`PlanValidatorTest` 4、`PlanViewModelTest` 3。
  - `PlanViewModelTest` 覆盖：7 秒限流→等待 3 秒→剩余 4 秒；冷却内重复 `generate()`/`retry()` 不增加 `createPlanJob`；切会话保留冷却并以新会话 ID 生成；计划已生成但首次 GET 失败时，重试只 GET 原计划（`createCalls` 不增）。
- APK：`android/app/build/outputs/apk/debug/app-debug.apk`，10,445,372 字节；包名 `com.tutorialcoach.app`，versionName `0.1.0`，minSdk 26 / targetSdk 35。

## 3. 真机复核

### 环境

- 设备：realme GT6 / RMX3800 / Android 16（SDK 36），1264×2780，adb `eeffd16b device`，设备代号 `RE5C4FL1`。
- 安装：`adb install -r app-debug.apk` → `Success`，冷启动成功，首页显示“服务端：正常”。
- 连接：`adb reverse tcp:8000 tcp:8000`，服务端监听 `127.0.0.1:8000`。

### 测试替身说明（重要）

本轮真机使用 **“真实服务端代码 + 测试模型替身”**（`work/device_review_test_server.py`，未跟踪、不提交）：

- 路由、存储、Job 创建、错误信封、错误码映射均走真实服务端代码；
- 只替换模型侧返回：`MODEL_RATE_LIMITED` + `retry_after_s`，或一次返回 10 条假设的固定草稿；
- **不是真实 DeepSeek 的 429 响应，也不是真实模型一次返回 10 条假设**；
- 临时测试服务端在验证后已停止，8000 端口已释放。

### 3.1 7 秒限流

1. 首页创建会话后进入计划页，点击“生成计划（真实模型）”。
2. 页面显示：“模型限流，请等待 6 秒后再试；等待期间不会创建新任务。”（`retry_after_s=7`，抓取时已过 1 秒）。
3. 错误区只显示“关闭”，不显示“重试”；生成按钮禁用。
4. 冷却内连续点击生成按钮 3 次：`server/data/jobs` 文件数保持 **15 → 15**（触发后基线 15）。
5. 冷却结束后“重试”按钮恢复、生成按钮可用；再次点击生成：Job 数 **15 → 16**。

### 3.2 切会话保留冷却（20 秒注入）

1. 新建会话并触发限流，页面显示“模型限流，请等待 19 秒后再试”；Job 数 17。
2. 返回首页再新建第二个会话进入计划页：
   - 仍显示“模型限流，请等待 2 秒后再试；等待期间不会创建新任务。”（两次会话创建耗时后剩余 2 秒，冷却未随会话切换丢失）；
   - 页面状态为“条件已就绪，点击下方按钮生成计划。”；
   - 没有旧会话的“出错了 / 模型限流，请稍后重试。”，旧错误未覆盖新会话。
3. 剩余冷却内点击生成按钮 2 次：Job 数保持 **17 → 17**。
4. 冷却结束后点击生成：Job 数 **17 → 18**；最新 Job 的 `session_id` 为 `sess_01M6NDZC4AF8E972XACP9XKX3B`，对应目标为 `second oup` 的新会话（`sess_01M6NDYJMXNF43N38QSPMGXGD8` 为前一会话）。

### 3.3 10 条假设

1. 以蘑菇汤目标创建会话并生成计划（测试模型替身返回 10 条假设）。
2. 计划页显示“假设”共 10 条：`模型假设 1` 至 `模型假设 9` 保持原顺序，第 10 条为
   “未提供过敏信息，请核对本次实际使用的食材和调味料；无法确认是否存在过敏原。”
3. 通用提示恰好出现 1 次；未出现番茄/鸡蛋/面条等固定菜谱食材。

### 3.4 设备端 UI 文本摘录

- 7 秒冷却：“模型限流，请等待 6 秒后再试；等待期间不会创建新任务。”
- 切会话新页面：“模型限流，请等待 2 秒后再试；等待期间不会创建新任务。” + “条件已就绪，点击下方按钮生成计划。”
- 10 条假设：“• 模型假设 1” … “• 模型假设 9” + “• 未提供过敏信息，请核对本次实际使用的食材和调味料；无法确认是否存在过敏原。”

## 4. 本地证据（不提交）

- `work/ui_home.xml`、`work/ui_plan_idle.xml`
- `work/ui_rate_limit_a.xml`、`work/ui_rate_limit_b.xml`、`work/ui_after_wait.xml`、`work/ui_after_wait2.xml`
- `work/ui_sess2_idle.xml`、`work/ui_sess2_rate_limit.xml`、`work/ui_new_session_rate_limit.xml`、`work/ui_new_session_after_wait.xml`
- `work/ui_ten_assumptions.xml`
- `work/device_rate7.log`、`work/device_rate20.log`、`work/device_ten.log`

`work/` 与截图均未提交；运行数据 `server/data/` 未提交。

## 5. 提交前密钥扫描

`server/.venv/Scripts/python.exe scripts/scan_secrets.py`：扫描 **191** 个文本文件，0 匹配，`clean=true`；结果见 `secret_scan_p2p3.json`。

## 6. 未验证边界

以下项目不得当作已通过：

- 真实 DeepSeek 恰好触发 429 并返回 `retry_after_s`（本轮为测试模型替身注入）；
- 真实模型一次返回 10 条假设（本轮为测试模型替身注入）；
- 7 秒→3 秒→4 秒的精确边界仅在 JVM 测试中覆盖；真机切会话场景使用 20 秒注入观察；
- 旋转、切后台、进程被杀后的恢复；
- 中文输入法直接输入目标（设备端 adb 只能注入 ASCII）；
- 截图 AI 视觉检查（结论来自 UI 层级文本与服务端日志）。