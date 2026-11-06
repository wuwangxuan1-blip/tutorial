# D5 配方解析优先级修复（第 7 轮）

基线：`0e254a2`（本地 `864b211` 仅文档状态记录，不改代码）。本轮只修总量/总时长的来源与优先级，不进入 D6。

## 总水量

- 分层解析：
  1. 显式总量：`总注水/总水量/注水总量/总水/总量/总计/合计/最终注水/最终水量`；存在显式总量时忽略任何阶段注水量。
  2. 无显式总量时，仅接受唯一累计终值：`继续注水至/注水至/注水到/加水至/加到/累计注水/累计水量`。
  3. 其余视为阶段/局部量；多个不同值或只有闷蒸/局部用水 → 422 `water_total_ambiguous`。
- 「闷蒸 30 g → 注水至 100 g → 注水至 150 g → 总水量 225 g」→ 225 g（ratio 1:15）。
- 「闷蒸注水 30 g，继续注水至 225 g」→ 225 g（回归保留）。
- 「注水至 100 g → 注水至 150 g」无总量 → 422（`source=terminal_pour`）。
- 「闷蒸 30 g」仅有局部量 → 422（`source=local_only`）。
- 失败时 `GET /v1/sessions/{id}/recipes` 为空，不创建配方。

## 总时长

- 显式 `总时长/总时间` 支持中英文冒号，先于任何单步用时：
  - `总时长：150 秒，闷蒸用时 30 秒` → 150 秒；
  - `闷蒸用时 30 秒，总时长：150 秒` → 150 秒；
  - `总时长: 2 分 30 秒，闷蒸用时 30 秒` → 150 秒。
- 多个不同显式总时长 → 422 `brew_time_ambiguous`。
- 调整 `brew_time_s=180` 只改写显式总时长标签（`总时长/总时间/时长`），`闷蒸用时 30 秒` 保持不变；旧版仍为 150 秒。

## API 回归

均通过 `POST /v1/sessions/{id}/recipes`、`GET /v1/recipes/{id}`、`POST /v1/recipes/{id}/adjustments` 校验实际保存的 `variables`、`ingredients`、`steps` 与历史版本。

## 本轮实测

- 服务端：`.venv/Scripts/python.exe -m pytest -o addopts=""` → **120 passed / 0 failed**（配方 14 项）。
- Android：`:app:testDebugUnitTest --rerun-tasks` → **55 tests / 0 failures**（本轮未改 Android）。
- `:app:assembleDebug --rerun-tasks` → BUILD SUCCESSFUL；APK **10,822,322 字节**。

## 状态分列

- 第三方实拍链路：通过；用户自拍环绕：BLOCKED；真机配方对比：BLOCKED；真机断网重试：BLOCKED；真机 easing/拖动未复测。
- 未进入 D6。