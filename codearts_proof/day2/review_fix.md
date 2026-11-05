# P1 复审修复验证（2026-11-05）

基线：`2d232e2`。本文件只记录三项复审修复，详细 D2 证据见同目录其他文件。

## 1. 模型限流等待

- `PlanViewModel` 新增 `PlanUiState.RateLimited(message, remainingSeconds)`；Job 失败 `MODEL_RATE_LIMITED` 时读取 `retry_after_s` 并每秒倒计时。
- 等待期间 `PlanScreen` 不显示生成/重试按钮；`generate()`、`retry()` 在 ViewModel 层再次拦截；`pollJob.isActive` 阻止重复 Job。
- 会话切换会取消倒计时并清零等待状态。
- 测试（JVM 测试替身，非真实模型/真机）：
  - `rateLimitBlocksGenerationAndRetryUntilWaitExpires`：7 秒内重复 generate/retry，createCalls 仍为 1；7 秒后手动重试 createCalls=2。
  - `sessionChangeClearsOldRateLimitState`：切换会话后状态回到 Idle，旧倒计时不阻塞新会话。
- 真机未注入 429；该 UI 路径本次仅 JVM 验证。

## 2. 两次非法 JSON 后 Job retryable

- `ModelClient` 的 `invalid_json` 错误现在 `MODEL_BAD_OUTPUT` + `retryable=true`。
- `PlanService` 首次非法 JSON 发起一次修复；第二次仍非法则 Job 失败。
- 测试：`test_two_invalid_json_http_responses_fail_job_with_retryable`
  - 使用真实 `ModelClient` + `httpx.MockTransport`，连续返回两次非法 JSON；
  - 断言 Job `MODEL_BAD_OUTPUT`、`retryable=true`、HTTP 调用次数恰好 2、计划未写入。
  - 未使用真实付费模型，也未直接构造预标记异常的 ApiError。

## 3. 过敏提示泛化

- 默认提示改为：“未提供过敏信息，请核对本次实际使用的食材和调味料；无法确认是否存在过敏原。”
- 未提供（`None`）才添加；用户明确回答“无”归一化为 `[]`，不添加该提示。
- 测试（假模型计划，验证真实服务端假设逻辑）：
  - `test_allergy_assumption_is_generic_for_mushroom_soup`：蘑菇汤目标，提示包含“本次实际使用的食材和调味料”，不含番茄/鸡蛋/面条。
  - `test_explicit_no_allergies_skips_generic_allergy_note`：`allergies=[]` 时不出现“未提供过敏信息”。
- 服务端真实流程已用番茄鸡蛋面重跑：5 步、8 条假设、30.837 s/5196 tokens，证明正常流程未受影响。

## 汇总

- 服务端：**47 passed**。
- 安卓：**21 passed**（0 失败）。
- APK：`android/app/build/outputs/apk/debug/app-debug.apk`，约 11 MB。
- 测试替身：限流 JVM 网关、非法 JSON 的 MockTransport、蘑菇汤假计划。
- 真实调用：D2 番茄鸡蛋面服务端真实计划（重跑）；真机未重新执行本轮三项修复。