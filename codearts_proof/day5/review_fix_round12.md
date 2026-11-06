# D5 连续调整的中途/最终目标身份保留（第 12 轮）

基线：`43b6e23`。修复连续调整总水量时“仅凭数值相同就把中途目标一并改写”的问题；未进入 D6。

## 问题

初始 `总水量 225 g，中途注水至 100 g，最后继续注水至 225 g 后停止`。先把总量改 100 g 后，显式总量与中途目标同为 100 g；再改 240 g 时，旧实现会把所有同值 terminal（含中途 100 g）都当作总量引用改写，导致中途注水被改成 240 g。

## 实现

- `_locate_water_spans` 在显式总量来源下只更新**最终目标** terminal：
  - 标签为 `继续注水至/继续注水到/最终注水/最终水量`；或
  - 数值后紧跟“后停止/即停止/后结束”。
- `注水至 X` 等中途累计目标即使与当前总量同值也不改写；最终停止目标继续随总量更新。
- 下限校验（新总量低于保留的中途目标 → 422 `intermediate_water_exceeds_total`）保留。

## API 回归

初始：`咖啡粉 15 g，总水量 225 g，中途注水至 100 g，最后继续注水至 225 g 后停止，水温 92 °C，总时长 150 秒。`

1. 改 90 g：422 `intermediate_water_exceeds_total`（`water_g=90`、`intermediate_targets=[100]`），不写入；v1 与历史保持原值。
2. 先改 100 g（v2）：总量/最终停止条件为 100 g，中途仍 100 g，`ratio=6.67`，用料水 100 g。
3. 再改 240 g（v3，基于 v2 id、`base_version=2`）：总量/最终停止条件为 240 g，中途仍 100 g，`ratio=16.0`，用料水 240 g。
4. 历史 `[1, 2, 3]`；v1 仍 225/100/225，v2 仍 100/100/100，均按原值回查。

既有回归（创建期来源校验、摘要来源 422、`注水 225 g`、跨步骤总时长、显式总量优先、冒号总时长、静置/闷蒸单步不改、多段/局部 422）全部保留并通过。

## 本轮实测

- 服务端：`.venv/Scripts/python.exe -m pytest -o addopts=""` → **129 passed / 0 failed**（配方 23 项）。
- Android：`:app:testDebugUnitTest --rerun-tasks` → BUILD SUCCESSFUL；**55 tests / 0 failures / 0 errors**（本轮未改 Android）。
- `:app:assembleDebug --rerun-tasks` → BUILD SUCCESSFUL（35 tasks executed）；APK **10,822,322 字节**。

## 状态分列

- 第三方实拍链路：通过；用户自拍环绕：BLOCKED；真机配方对比：BLOCKED；真机断网重试：BLOCKED；真机 easing/拖动未复测。
- 未进入 D6。