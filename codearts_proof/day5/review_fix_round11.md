# D5 总水量下限校验（第 11 轮）

基线：`f840d03`。总水量调整后、写入新版本前校验仍保留的中途累计注水目标；未进入 D6。

## 实现

- 调整总水量时先按来源定位器得到要更新的 span（显式总量、同值最终停止条件、同值普通声明）。
- 收集步骤中**未被本次更新**的中途累计注水目标（`注水至/继续注水至/累计注水/注水`）；若新总水量低于任一目标，返回 422 `INVALID_REQUEST`（`intermediate_water_exceeds_total`，`details.water_g`、`details.intermediate_targets`），不创建新版本。
- 失败不影响旧版本与历史；成功时中途目标保持原值，最终停止条件同步为新总量。

## API 回归

原配方：`总水量 225 g，中途注水至 100 g，最后继续注水至 225 g 后停止`。

- 总量改 90 g：422 `intermediate_water_exceeds_total`，`water_g=90`、`intermediate_targets=[100]`；配方列表与历史仍只有 v1，旧版参数/步骤不变。
- 总量改 240 g：201；新版 `water_g=240`、`ratio=16.0`、用料水 240 g；`中途注水至 100 g` 不变，`继续注水至 240 g 后停止` 在 instruction 与 target 同步；旧版仍 225 g / 100 g；历史 `[1, 2]`。

保留回归：摘要来源创建期 422（水/时长各一例）、创建期来源校验、停止条件同步、`注水 225 g`、跨步骤总时长、显式总量优先、冒号总时长、静置/闷蒸单步不改、多段/局部 422 全部通过。

## 本轮实测

- 服务端：`.venv/Scripts/python.exe -m pytest -o addopts=""` → **128 passed / 0 failed**（配方 22 项）。
- Android：`:app:testDebugUnitTest --rerun-tasks` → BUILD SUCCESSFUL；**55 tests / 0 failures / 0 errors**（本轮未改 Android）。
- `:app:assembleDebug --rerun-tasks` → BUILD SUCCESSFUL（35 tasks executed）；APK **10,822,322 字节**。

## 状态分列

- 第三方实拍链路：通过；用户自拍环绕：BLOCKED；真机配方对比：BLOCKED；真机断网重试：BLOCKED；真机 easing/拖动未复测。
- 未进入 D6。