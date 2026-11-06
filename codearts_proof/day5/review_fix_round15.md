# D5 总量冲突检测与 Android 确认流程（第 15 轮）

基线：`3c86b6e`。两项修复：总量与最终停止条件冲突检测；旧配方确认流程接入 Android。未进入 D6。

## 1. 总量冲突检测

- 显式总量与明确最终停止条件值不同：`总水量 225 g，最后注水至 220 g 后停止` → 422 `INVALID_REQUEST`（`water_total_conflicts_with_final`，`details.water_g=225`、`details.final_targets=[220]`）。
- 创建、旧配方恢复、调整三条路径均拦截，不写入冲突版本。
- 正常用例保留：中途累计量低于总量（如 100 < 225）；225→100→240 连续调整；90 g 被拒绝且不写入。

## 2. Android 确认流程

- `ApiException` 暴露 `details`；解析 `confirmation_required`、`confirm_field`、`candidates`。
- 配方页弹出确认对话框：展示每个候选的步骤号、字段（执行步骤/完成条件）、标签与数值；用户分别勾选“总量”和“最终”。
- 确认后沿用原调整参数与 `base_version` 重试，携带 `water_source_confirmation.declaration/final`。
- 取消：关闭弹窗，不发送请求，不创建版本。
- 重试遇 409：显示版本冲突并刷新最新版本。
- JVM 测试覆盖：确认成功（请求携带原 base_version 与候选 ID）、取消（无第二次请求）、版本冲突（显示刷新提示）。

## 本轮实测

- 服务端：`.venv/Scripts/python.exe -m pytest -o addopts=""` → **136 passed / 0 failed**（配方 30 项）。
- Android：`:app:testDebugUnitTest --rerun-tasks` → BUILD SUCCESSFUL；**58 tests / 0 failures / 0 errors**。
- `:app:assembleDebug --rerun-tasks` → BUILD SUCCESSFUL（35 tasks executed）；APK **10,838,706 字节**。

## 状态分列

- 第三方实拍链路：通过；用户自拍环绕：BLOCKED；真机配方对比：BLOCKED；真机断网重试：BLOCKED；真机 easing/拖动未复测。
- 未进入 D6。