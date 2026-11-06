# D5 中途完成条件区分与确认完整性（第 16 轮）

基线：`3472e54`。三项修复，未进入 D6。

## 1. 中途完成条件不是最终停止条件

- 中途步骤 `target` 中的 `注水至 100 g` 不再被冲突检测当作最终条件；只有最后一个执行步骤的最终目标（或带“最后/最终/后停止/后结束”标记）才是最终条件。
- 回归：总水量 225 g、中途完成条件 `注水至 100 g`、最后 `注水至 225 g 后停止` 可创建；改 240 g 后中途仍 100 g，最终 240 g，用料 240 g，旧版 225 g。
- 真正的最终条件冲突（`总水量 225 g，最后注水至 220 g 后停止`）仍返回 422 `water_total_conflicts_with_final`，不写入。

## 2. 服务端确认完整性与 Android 提示

- 存在最终指令时，只选声明、遗漏最终 → 422 `invalid_water_source_confirmation`（`missing=["final"]`、`requires_final=true`），不写入新版本。
- 候选包含 `text` 原文片段；Android 弹窗展示“步骤 N · 原文片段”。
- Android 在 `requiresFinal=true` 且未选最终时提示“请选择最终执行指令”，不发送重试请求。
- 测试：确认成功、遗漏最终、取消、版本冲突。

## 3. 类型化确认请求

- `WaterSourceConfirmation`：`declaration` 至少 1 项，`final` 可空；严格整数、非负（Pydantic strict）。
- 服务端校验候选 ID 范围、角色（final 必须 terminal 且值等于当前总量）；非法类型/范围/角色 → 422 `invalid_water_source_confirmation`，不写入新版本。

## 回归保留

225→100→240 连续调整、90 g 拒绝不写入、历史版本原值回查、旧配方自动恢复/确认、显式总量优先、冒号总时长、静置/闷蒸单步不改。

## 本轮实测

- 服务端：`.venv/Scripts/python.exe -m pytest -o addopts=""` → **137 passed / 0 failed**（配方 **31**）。
- Android：`:app:testDebugUnitTest --rerun-tasks` → BUILD SUCCESSFUL；**59 tests / 0 failures / 0 errors**。
- `:app:assembleDebug --rerun-tasks` → BUILD SUCCESSFUL（35 tasks executed）；APK **10,838,706 字节**。

## 状态分列

- 第三方实拍链路：通过；用户自拍环绕：BLOCKED；真机配方对比：BLOCKED；真机断网重试：BLOCKED；真机 easing/拖动未复测。
- 未进入 D6。