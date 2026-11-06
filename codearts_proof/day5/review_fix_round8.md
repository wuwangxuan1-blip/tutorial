# D5 配方创建与调整总量一致性（第 8 轮）

基线：`991b4b6`。创建与调整共用同一套来源识别规则，只更新被识别为总量/总时长的位置，不按标签片段或相同数字改写单步用量与用时。未进入 D6。

## 共用规则

- 解析与改写使用同一组常量与正则：
  - 水量：`_WATER_MENTION_PATTERN` + 显式/终值/阶段/局部分类（`_WATER_EXPLICIT_LABELS`、`_WATER_TERMINAL_LABELS`、`_WATER_LOCAL_LABELS`）。
  - 时长：`_TOTAL_TIME_PATTERN`（显式总时长，支持中英文冒号）与 `_STEP_TIME_PATTERN`（单步时长，排除静置/闷蒸/单步标签）。
- 改写按识别出的字符位置（span）精确替换，不再用宽泛标签正则扫描并替换。

## 总水量

- 创建：显式总量 > 唯一累计终值 > 唯一普通水量；多值歧义仍 422 `water_total_ambiguous`。
- 调整：字段内存在显式总量时只改显式总量，并同步同值普通水量声明（`水/水量`）；无显式时改唯一终值或普通水量声明。
- 阶段注水（`注水至 100 g`）、闷蒸局部量（`闷蒸 30 g`）、温杯/润洗用水不改。
- 回归：`注水总量：225 g` → 240 g，新版参数 `water_g=240`、`ratio=16.0`、用料水 240 g、步骤 `注水总量：240 g`；`注水至 100 g`、`闷蒸 30 g` 保持；旧版仍为 225 g。

## 总时长

- 创建：显式 `总时长/总时间` 优先，多个不同值 422 `brew_time_ambiguous`。
- 调整：只改显式总时长的 expression span；`静置时长`、`闷蒸用时` 等单步时长不改。
- 回归：`总时长：150 秒，静置时长 150 秒` → 180 秒后，新版仅 `总时长：180 秒`，`静置时长 150 秒` 保留；旧版仍为 150 秒。

## 保留的上轮用例

- 显式总水量优先于阶段注水（闷蒸 30→100→150 + 总水量 225 = 225 g）。
- 中英文冒号总时长优先于单步用时。
- 无显式总量时多段注水/仅闷蒸局部量 → 422 且不创建配方。
- 步骤改写不全局替换数字；旧版本只读保留。

## API 回归

均通过 `POST /v1/sessions/{id}/recipes`、`GET /v1/recipes/{id}`、`POST /v1/recipes/{id}/adjustments`、`GET /v1/recipes/{id}/history` 校验实际保存的 `variables`、`ingredients`、`steps` 与历史版本。

## 本轮实测

- 服务端：`.venv/Scripts/python.exe -m pytest -o addopts=""` → **122 passed / 0 failed**（配方 16 项）。
- Android：`:app:testDebugUnitTest --rerun-tasks` → **55 tests / 0 failures**（本轮未改 Android）。
- `:app:assembleDebug --rerun-tasks` → BUILD SUCCESSFUL；APK **10,822,322 字节**。

## 状态分列

- 第三方实拍链路：通过；用户自拍环绕：BLOCKED；真机配方对比：BLOCKED；真机断网重试：BLOCKED；真机 easing/拖动未复测。
- 未进入 D6。