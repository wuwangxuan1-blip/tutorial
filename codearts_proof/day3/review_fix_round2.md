# D3 复审修复第二轮（2026-11-05）

基线：`8fb655c`。本轮只修复 Codex 复审提出的 2 项问题。

## 1. [P1] remove 后再 update/reorder 同一步骤

- `server/app/services/revision_service.py` 的 `_validate_changes` 新增顺序校验：
  - 按 changes 顺序维护可用步骤 ID 与剩余步数；
  - `remove` 后从可用集合移除该步骤并递减；
  - 后续 `update`/`reorder`/`remove` 引用该步骤时返回 **422 `INVALID_REQUEST`**，`details.reason=step_removed_by_revision`；
  - `add` 顺序校验时增加剩余步数。
- `apply()` 使用顺序校验，并继续在校验完整候选计划 `PlanOut` 后才执行 `save_plan/save_session/save_revision`。
- 新增 API 回归（`server/tests/test_revisions.py`）：
  - `test_revision_apply_rejects_update_of_removed_step`
  - `test_revision_apply_rejects_reorder_of_removed_step`
  - 均断言：旧计划 v1/3 步、会话版本 1、进度 `step_2=in_progress` 保持、修订仍 `proposed`、`load_plan(session,2)` 为空。

## 2. [P2] 旧 finished PATCH 未返回时重置计时

- `StepViewModel` 新增 `timerEpoch` 与 `beginTimerChange()`：
  - 任何计时变更（开始/暂停/继续/重置/前进/完成/跳过/暂停练习）先递增 epoch 并取消旧 ticker；
  - `ensureTicker()` 捕获 epoch，旧协程在继续、tick、finished PATCH 前检查 epoch；过期协程不再写入状态；
  - 重置时立即取消旧 ticker，因此即使旧 finished PATCH 挂起，新的刷新协程也会启动。
- 新增回归 `resetWhileFinishedPatchPendingKeepsNewCountdown`：
  - fake gateway 用 `CompletableDeferred + NonCancellable` 挂起 finished PATCH；
  - 计时自然结束 → 重置 → 推进 5 秒，新倒计时下降；
  - 释放旧响应 → 状态仍为新的 running 计时；
  - 再推进 2 秒，剩余秒数继续下降。

## 结果

- 服务端：**76 passed / 0 failed**（test_revisions 由 8 增至 10）。
- Android：**34 passed / 0 failed**（StepViewModelTest 由 7 增至 8）。
- `assembleDebug` BUILD SUCCESSFUL；APK `android/app/build/outputs/apk/debug/app-debug.apk`，10,639,369 字节。
- `git diff --check` 通过；密钥扫描 226 文件、0 匹配、`clean=true`。
- 真机未在本轮重跑；两项修复待复审后补设备验证。