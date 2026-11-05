# D3 复审三项修复（2026-11-05）

基线：`ab3fbfa` 之上的 D3 工作区改动。本轮只修复 Codex 复审提出的 3 项问题，不改范围。

## 1. [P1] 修订不得写入无效计划

- `server/app/services/revision_service.py` 的 `apply()` 在应用完全部 changes 后、任何 `save_plan/save_session/save_revision` 之前，构造完整候选计划并用 `PlanOut` 校验。
- 校验失败返回 422 `INVALID_REQUEST`，`details.reason=revision_plan_invalid`；原计划、会话 `current_plan_version`、进度和修订 `proposed` 状态保持不变。
- 新增回归：
  - `test_revision_apply_rejects_remove_below_minimum`：3 步删 1 步 → 422；GET /plan 仍为版本 1、3 步；修订仍 `proposed`。
  - `test_revision_apply_rejects_add_above_maximum`：15 步加 1 步 → 422；GET /plan 仍为版本 1、15 步。
  - `test_revision_apply_rejects_combined_removes_below_minimum`：3 步连续删 2 步（单项校验通过、组合后仅 1 步）→ 422；原计划不变。

## 2. [P2] 完成/跳过与自动前进合并为一次 PATCH

- `StepViewModel.completeStep()`/`skipStep()` 不再先写当前步、再单独 PATCH 下一步。
- 一次请求包含：当前步 `done`（完成时附 `self_reported`）或 `skipped`、`current_step_id`、计时器变更；下一步仅在状态缺失或 `not_started` 时加入 `in_progress`。
- 下一步已是 `done`/`skipped`/`in_progress` 时不发送状态，服务端保留原状态与证据。
- PATCH 失败时不更新界面索引，仍停留在当前步并显示错误。
- 新增回归：
  - `completeStepKeepsDoneNextStepAndUsesSinglePatch`
  - `skipStepKeepsSkippedNextStepAndUsesSinglePatch`
  - `completeStepFailureDoesNotAdvance`

## 3. [P2] 重置计时器后重启刷新协程

- `StepViewModel.resetTimer()` 在 PATCH 成功后调用 `ensureTicker()`；`confirmTimerReset()` 复用 `resetTimer()`。
- `ensureTicker()` 仅在现有 ticker 未激活时启动新协程，保证同一时刻只有一个刷新任务。
- 新增回归：
  - `resetAfterNaturalFinishRestartsTicker`：计时自然结束 → 重置 → 推进 5 秒，剩余秒数继续下降。
  - `confirmTimerResetRestartsTicker`：无效锚点触发确认 → 重置 → 推进 5 秒，剩余秒数继续下降。

## 结果

- 服务端：`71 → 74 passed`（新增 3 项修订回归）。
- Android：`28 → 33 passed`（StepViewModelTest 从 2 增至 7）。
- `assembleDebug` BUILD SUCCESSFUL；APK `android/app/build/outputs/apk/debug/app-debug.apk`，10,576,503 字节。
- `git diff --check` 通过；密钥扫描 223 文件、0 匹配、`clean=true`。
- 真机未在本轮重跑；三个修复点的设备行为待 Codex 复审后验证。