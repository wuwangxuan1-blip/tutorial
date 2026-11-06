# D5 总量来源身份持久化（第 13 轮）

基线：`a90c82a`。把总量声明与最终停止条件的身份持久化，跨版本复用；未进入 D6。

## 问题

`继续注水至` 既可能是中途动作，也可能是最终动作，不能单独作为最终判据；此前每次调整都从自由文本重新猜测，连续调整时中途目标与最终目标同值会被一起改写。

## 实现

- `Recipe` 新增可选 `total_sources`；创建时记录 `water_g` 的 marks：
  - `step_index`、`field`（instruction/target）、`label`、`kind`、`ordinal`（同字段同标签序号）、`role=declaration|final`。
  - 最终判定不再看标签，只看值后“后停止/后结束”或前文“最后/最终”。
- 调整时按 marks 定位并更新 declaration/final，不再自由文本猜测；marks 跨版本原样保留。
- 旧配方无 `total_sources` 或定位失败 → 422 `total_source_unconfirmed`，不写入。
- 下限校验保留：新总量低于仍保留的中途累计注水目标 → 422 `intermediate_water_exceeds_total`。

## API 回归

计划：`咖啡粉 15 g，总水量 225 g，闷蒸后继续注水至 100 g，等待 10 秒，水温 92 °C，总时长 150 秒。`，完成条件 `注水至 225 g 后停止`。

1. 改 90 g：422 `intermediate_water_exceeds_total`，不写入。
2. 先改 100 g（v2）：总量与最终停止条件 100 g，中途 `继续注水至 100 g` 不变，等待 10 秒不变。
3. 再改 240 g（v3，基于 v2 id）：总量与最终停止条件 240 g，中途仍 100 g、等待仍 10 秒；用料水 240 g。
4. 历史 `[1,2,3]`；v1 仍 225/100/225，v2 仍 100/100/100。
5. 无 marks 的旧配方调整 → 422 `total_source_unconfirmed`。

既有回归（显式总量优先、注水总量按位置改写、冒号总时长、静置/闷蒸单步不改、多段/局部 422、`注水 225 g`、跨步骤总时长、连续调整身份）全部保留并通过。

## 本轮实测

- 服务端：`.venv/Scripts/python.exe -m pytest -o addopts=""` → **131 passed / 0 failed**（配方 25 项）。
- Android：`:app:testDebugUnitTest --rerun-tasks` → BUILD SUCCESSFUL；**55 tests / 0 failures / 0 errors**（本轮未改 Android）。
- `:app:assembleDebug --rerun-tasks` → BUILD SUCCESSFUL（35 tasks executed）；APK **10,822,322 字节**。

## 状态分列

- 第三方实拍链路：通过；用户自拍环绕：BLOCKED；真机配方对比：BLOCKED；真机断网重试：BLOCKED；真机 easing/拖动未复测。
- 未进入 D6。