# D5 最后执行指令身份与旧配方恢复（第 14 轮）

基线：`ad81680`。修复两项：最后执行指令的结构化判定、旧配方缺少 `total_sources` 的恢复路径；未进入 D6。

## 1. 最后执行指令

- 不再靠追加停止关键词；最终目标按结构判断：
  - 若全部终值都与总量同值，则它们都是总量引用；
  - 若存在不同值的中途目标，则只把最后一个执行步骤中与总量同值的终值（且该步骤内这些终值全部为 `target` 或带“后停止/后结束/最后”标记）标记为 final；
  - 无法确认时创建前返回 422 `total_source_unconfirmed`，不创建配方。
- 回归：`总水量 225 g` + `分两次注水至 225 g，等滤杯滴完` 改 240 g 后，参数、用料与最后执行指令均为 240 g；旧版仍 225 g。

## 2. 旧配方恢复

- 缺少 `total_sources` 时，首次调整若能在步骤文本中唯一确认来源，自动补齐 marks 并写入新版本；旧版本与历史保持原值。
- 同值歧义（中途与最终同值、跨步骤同值）返回 422 `total_source_unconfirmed`：
  - `details.confirmation_required=true`
  - `details.confirm_field=water_source_confirmation`
  - `details.candidates` 给出候选 `candidate_id`、步骤、字段、标签、值。
- 客户端可携带 `water_source_confirmation.declaration/final`（候选 ID 数组）重试；服务端校验后写入新版本，历史原值保留。
- 回归：旧配方首次调整自动补齐并成功；同值歧义先 422、确认后 201；v1 历史按原值回查。

## 保留回归

- 225→100→240 连续调整，中途 100 g 不变；
- 90 g 低于中途目标 → 422 `intermediate_water_exceeds_total` 且不写入；
- 显式总量优先、`注水总量` 按位置改写、冒号总时长、静置/闷蒸单步不改、多段/局部 422。

## 本轮实测

- 服务端：`.venv/Scripts/python.exe -m pytest -o addopts=""` → **134 passed / 0 failed**（配方 28 项）。
- Android：`:app:testDebugUnitTest --rerun-tasks` → BUILD SUCCESSFUL；**55 tests / 0 failures / 0 errors**（本轮未改 Android）。
- `:app:assembleDebug --rerun-tasks` → BUILD SUCCESSFUL（35 tasks executed）；APK **10,822,322 字节**。

## 状态分列

- 第三方实拍链路：通过；用户自拍环绕：BLOCKED；真机配方对比：BLOCKED；真机断网重试：BLOCKED；真机 easing/拖动未复测。
- 未进入 D6。