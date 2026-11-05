# D5 复审修复（2026-11-05，三项）

基线：`fb05fde`。只修以下三项，不进入 D6。

## 1. 配方创建使用用户已确认的计划参数

- `RecipeCreateRequest` 新增 `demo`（默认 `false`）。
- `demo=false`：从计划文本解析已确认的咖啡粉量、水量、水温、总时长，派生粉水比；缺少/越界直接 422 `INVALID_REQUEST`，不再对 V60/手冲静默套用 15 g/225 g/92 °C/150 秒。
- `demo=true`：仅表示用户明确选择 V60 演示配方；当前计划参数必须与 15 g/225 g/92 °C/150 秒一致，否则 422 `demo_parameters_mismatch` 且不创建配方。
- Android 配方页新增“明确使用 V60 演示参数”勾选；默认按钮为“按计划参数创建配方”。
- 回归：`test_recipe_uses_confirmed_plan_parameters_and_demo_requires_matching_plan`
  - 非默认 18 g / 270 g / 90 °C / 165 秒计划 → 配方参数一致，步骤说明含 18 g/270 g/90 °C/165 秒；
  - 默认计划 + demo=true → 固定 15/225/92/150；
  - 非默认计划 + demo=true → 422，且会话无配方。

## 2. 用户可编辑变量与粉水比派生规则

- 契约与实现明确：
  - 用户可编辑：`dose_g`、`water_g`、`water_temp_c`、`grind_setting`、`brew_time_s`、`milk_ml`、`ice_g`、`sweetener_g`；
  - `ratio` 为派生变量，不可直接编辑；直接请求返回 422 `INVALID_REQUEST`（`derived_variable`）。
- 当粉量与水量都存在时，`ratio = round(water_g / dose_g, 2)`。
- 只主动改水量 225→240 g 时，粉水比 15→16 属派生更新，**不构成第二个主动调整**；对比说明会明确“主动改变 water_g；粉水比派生更新”。
- 新版本同步更新 `variables`、`ingredients` 与步骤 instruction/target 中的参数文本；旧版本保持原值只读。
- 回归：`test_water_only_adjustment_derives_ratio_and_rewrites_recipe`
  - v2：water 240、ratio 16、用料水 240、步骤含 240 g 且不含 225 g；
  - v1 仍为 225/15、用料 225、步骤保留 225 g；
  - compare 同时显示 water_g Δ15 与派生 ratio Δ1，notes 说明派生。
- 回归：`test_derived_ratio_and_failed_adjustments_do_not_write`
  - 直接改 ratio → 422 `derived_variable`；
  - 同时改 water_g + water_temp_c → 422 `SINGLE_VARIABLE_REQUIRED`；
  - 非法水温 → 422；
  - 以上均未写入新版本。
- 既有 92→90、版本冲突、无实际变化回归继续通过。

## 3. Canvas 应用 CameraMoveSpec easing

- 新增 `CameraEasing`：`linear`、`ease_in`、`ease_out`、`ease_in_out`。
- Canvas 的位置、变焦、原地转向全部使用 `easedProgress = CameraEasing.easedProgress(spec.easing, playback.progress)`；时间轴文本仍显示真实时间 `progress * duration_s`。
- 拖动时间轴继续使用 `CameraPlaybackState.seek()`，拖动后暂停。
- 回归：`CameraEasingTest`
  - 同一中间时刻 0.25：linear=0.25，ease_in_out=0.125，画面进度不同；
  - 0.5→0.5、0.75→0.875、边界 clamp；
  - `CameraPlaybackStateTest` 覆盖 seek 0.4/1.4 与播放状态。

## 本轮实测

- 服务端：`pytest -o addopts=""` → **111 passed / 0 failed**（配方测试由 2 增至 5）。
- Android：`:app:testDebugUnitTest --rerun-tasks` → **55 tests / 0 failures**（`CameraEasingTest` 2、`RecipeViewModelTest` 4）。
- `:app:assembleDebug` → BUILD SUCCESSFUL；APK **10,896,532 字节**。
- 真实模型 V60（未选 demo，按计划参数解析）：v1 15/225/15/92/150 → 用户测试输入 tasting → water_temp_c 90 → v2；compare `92→90, delta -2`。

## 状态分列（不互相替代）

- **第三方实拍链路：通过**。照片 `unclear`；短片主反馈 `unclear`，4/4 证据帧字节一致；倒咖啡反例 `not_met`，5/5 帧字节一致（见 `third_party/`）。
- **用户自拍环绕验收：BLOCKED**。没有用户自拍的“手机环绕咖啡 8 秒”素材。
- **真机配方对比：BLOCKED**。真机 v1 与用户评分已通过 UI 保存（服务端 201）；92→90 调整与对比未在真机完成（按钮点击命中/权限限制）。
- **真机断网重试：BLOCKED**。已建立断开状态，但调整按钮未触发请求，未取得“错误→恢复→重试成功”证据。
- **真机时间轴拖动/easing：未复测**，由 JVM 覆盖。
- 未调整提示词；第三方真实验证无需复验。