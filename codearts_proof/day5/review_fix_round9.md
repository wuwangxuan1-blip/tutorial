# D5 配方调整总量来源定位（第 9 轮）

基线：`ac538ef`。创建与调整共用整份配方的来源定位规则；调整只更新已认定的总量引用，不逐字段猜测；旧配方无法安全定位来源时提示用户确认。未进入 D6。

## 共用来源规则

- 总水量：`_select_water_total` 同时服务创建与调整，优先级为显式总量 > 唯一累计终值 > 唯一普通水量声明（`注水/水/水量`），局部闷蒸量不参与。
- 总时长：显式 `总时长/总时间` 优先；无显式时仅接受全配方唯一的单步时长（排除静置/闷蒸/单步标签）。
- 调整时一次性扫描全部步骤字段确定来源，再按字段与字符位置（span）更新；不在每个字段内独立猜测。

## API 回归

1. `注水 225 g` 创建后改 240 g：新版 `water_g=240`、`ratio=16.0`、用料水 240 g、步骤 `注水 240 g`；旧版仍 225 g。
2. 步骤 0 写 `总时长：150 秒`、步骤 1 写 `萃取用时 150 秒`：总时长改 180 秒后，仅 `总时长：180 秒`，步骤 1 的 `萃取用时 150 秒` 不变；旧版两处均 150 秒。
3. 旧配方若无法在步骤文本中安全定位来源（本轮用例把总水量写在 summary）：调整返回 **422 `total_source_unconfirmed`**（`details.variable=water_g`），提示用户确认，配方仍只有 v1、原值不变。

均通过 `POST /v1/sessions/{id}/recipes`、`GET /v1/recipes/{id}`、`POST /v1/recipes/{id}/adjustments`、`GET /v1/recipes/{id}/history` 校验实际保存的 `variables`、`ingredients`、`steps`。

## 保留的上轮回归

- 显式总水量优先于阶段注水；`注水总量：240 g` 按位置改写且阶段注水/闷蒸量不变。
- 中英文冒号总时长优先；静置/闷蒸单步时长不改。
- 无显式总量时多段注水/仅闷蒸局部量 → 422 且不创建。
- 现有 16 项配方用例全部保留并通过。

## 本轮实测

- 服务端：`.venv/Scripts/python.exe -m pytest -o addopts=""` → **125 passed / 0 failed**（配方 19 项）。
- Android：`:app:testDebugUnitTest --rerun-tasks` → **55 tests / 0 failures**（本轮未改 Android）。
- `:app:assembleDebug --rerun-tasks` → BUILD SUCCESSFUL；APK **10,822,322 字节**。

## 状态分列

- 第三方实拍链路：通过；用户自拍环绕：BLOCKED；真机配方对比：BLOCKED；真机断网重试：BLOCKED；真机 easing/拖动未复测。
- 未进入 D6。