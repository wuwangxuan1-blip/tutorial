# D3 复审修复第三轮（计时失败恢复，2026-11-05）

基线：`1188238`。本轮只修 D3 剩余 P2：计时相关 PATCH 失败后，仍有效的运行中计时器必须继续倒计时。

## 修复

- `StepViewModel.beginTimerChange()` 在 PATCH 前取消 ticker；因此失败路径需要恢复刷新。
- `runAction` 增加可选 `epoch`：
  - 计时相关动作以 `runAction(epoch)` 调用；
  - 失败时仅当 `epoch == timerEpoch` 才显示错误，并调用 `restoreTickerIfRunning()`；
  - `restoreTickerIfRunning()` 仅在 `state.timer.state == "running"` 时调用 `ensureTicker()`；
  - 过期请求（epoch 已变化）的失败不显示错误、不恢复 ticker、不清除较新操作的 saving 状态。
- 计时失败时状态更新仍被 epoch 守卫拦截，界面不会提前前进或改成失败的新计时值。

## 回归测试（`StepViewModelTest`）

- `completeStepPatchFailureShowsErrorAndKeepsCounting`：运行中计时 → 完成 PATCH 失败 → 错误显示、索引仍为 0、剩余秒数继续下降。
- `resetTimerPatchFailureKeepsOldRunningTimerCounting`：运行中计时 → 重置 PATCH 失败 → 旧 running 计时保留（不显示重置后的 60 秒），倒计时继续。
- `staleTimerFailureDoesNotAffectNewerTimerOperation`：可挂起 fake 让旧重置失败请求悬而未决 → 新重置成功 → 释放旧失败 → 无错误、新计时保持并继续下降。
- 保留 `resetWhileFinishedPatchPendingKeepsNewCountdown`：旧 finished PATCH 与重置交错时新倒计时持续。

## 结果

- 服务端：**76 passed / 0 failed**（本轮未改服务端）。
- Android：**37 passed / 0 failed**（StepViewModelTest 由 8 增至 11）。
- `assembleDebug` BUILD SUCCESSFUL；APK `android/app/build/outputs/apk/debug/app-debug.apk`，10,639,798 字节。
- `git diff --check` 通过；真机未重跑，失败恢复路径待复审后补验证。