# D5 配方创建期来源固化与停止条件同步（第 10 轮）

基线：`b7e923c`。把参数来源从“调整时定位”前移到“创建时校验并固化”，并让总量与最终停止条件同步更新；未进入 D6。

## 实现

- 创建配方生成步骤后，用与调整共用的来源定位器校验 `water_g` 与 `brew_time_s` 能在 `instruction`/`target` 中定位；若总水量/总时长只出现在标题或摘要，**创建前**返回 422 `INVALID_REQUEST`（`total_source_unconfirmed`，`details.variable`），提示先在计划步骤中明确参数，避免创建成功后才暴露“无法调整”。
- 调整总水量时，除显式总量与同值 `水/水量` 声明外，**同值的终值/最终停止条件**（`继续注水至 225 g 后停止`）同步更新；中途不同值的阶段注水（`注水至 100 g`）保持原值。
- 旧配方直接调用定位器仍返回 422 `total_source_unconfirmed`，保留明确兜底。

## API 回归

1. `咖啡粉 15 g，总水量 225 g，中途注水至 100 g，最后继续注水至 225 g 后停止，水温 92 °C，总时长 150 秒。`
   - 创建：`water_g=225`；instruction 与 target（completion criteria）均含“继续注水至 225 g 后停止”。
   - 改 240 g：新版 `water_g=240`、`ratio=16.0`、用料水 240 g；instruction 为“总水量 240 g”“中途注水至 100 g”“继续注水至 240 g 后停止”，target 同步 240 g；旧版仍 225 g / 100 g。
2. 总水量只写在 summary：创建返回 422 `total_source_unconfirmed`（`variable=water_g`），message 含“摘要”，配方列表为空；总时长只写在 summary 时同理返回 `variable=brew_time_s`。
3. 旧数据兜底：对无水量来源的步骤调用定位器返回 422 `total_source_unconfirmed`。

既有 19 项配方回归（显式总量优先、注水总量按位置改写、冒号总时长、静置/闷蒸单步不改、多段/局部 422、`注水 225 g`、跨步骤总时长）全部保留并通过。

## 本轮实测

- 服务端：`.venv/Scripts/python.exe -m pytest -o addopts=""` → **127 passed / 0 failed**（配方 21 项）。
- Android：`:app:testDebugUnitTest --rerun-tasks` → BUILD SUCCESSFUL；**55 tests / 0 failures / 0 errors**（本轮未改 Android）。
- `:app:assembleDebug --rerun-tasks` → BUILD SUCCESSFUL（35 tasks executed，重跑一次仍成功）；APK **10,822,322 字节**。

## 状态分列

- 第三方实拍链路：通过；用户自拍环绕：BLOCKED；真机配方对比：BLOCKED；真机断网重试：BLOCKED；真机 easing/拖动未复测。
- 未进入 D6。