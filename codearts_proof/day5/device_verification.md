# D5 真机验收记录（2026-11-05）

- 设备：realme GT6 / RMX3800 / Android 16，adb 序列号 `eeffd16b`。
- APK 安装：`Success`；`adb reverse tcp:8000 tcp:8000` 成功；服务端 health `ok`，已确认加载 D5 配方端点。

## 摄影运镜（播放/暂停/重播已完成）

- 新建摄影会话（目标 `orbit a coffee cup 8 seconds vertical`，初学者、手持、9:16）后，真实模型生成 4 步计划，第 2 步 `机位与运镜预演` 含合法 `camera_move`：`orbit_cw`、8 秒、`ease_in_out`、9:16、2D 俯视局限说明。
- 步骤卡显示“运镜示意 / 机位移动 / 主体：咖啡杯 · orbit_cw · 8 秒”，并显示时间轴与播放/暂停/重播。
- 播放推进到 3.4/8.0 秒；暂停后停在 1.2 秒，间隔 5 秒仍为 1.2；重播后重新推进。截图：`device_camera_playing.png`、`device_camera_paused.png`。
- 本轮代码新增“拖动时间轴”及 `CameraPlaybackState.seek()` 回归（JVM 覆盖 0.4→0.4、1.4→1.0 且暂停播放）；新 APK 已安装，但真机时间轴拖动未再次走查（工具权限限制）。
- 旧 D4 计划 `visual_aid=null` 不可播；必须新建摄影会话。服务端对“环绕”文字但模型缺 spec 的计划生成带“非模型输出”说明的结构化 2D 兜底。

## 咖啡配方

已完成（真机）：
- 真实模型生成 V60 计划：15 g 咖啡粉、225 g 水、92 °C、约 2 分 30 秒；含设备替代提示。
- 计划页“打开咖啡配方”→ 从当前计划创建 v1；真机参数：咖啡粉 15 g、水 225 g、粉水比 1:15、水温 92 °C、研磨中细、总时长 150 秒。
- 品尝表单提示“模型不会从照片推断口味或萃取结果”。通过真机 UI 填写并保存：酸 4、甜 3、苦 2、醇厚 3、香气 4、余韵 3、总体 4，描述 `sour mild finish short`；服务端日志显示 `POST /v1/recipes/{id}/tastings` 返回 201，历史区显示该用户评分。该评分由验收操作者通过 UI 填写，不是模型推断。
- 单变量调整已填写 `water_temp_c=90` 与原因；`adb reverse --remove tcp:8000` 后尝试提交，但按钮点击未触发请求（页面无错误、无新版本），恢复 reverse 后同样未完成提交；多次点击/长按的操作随后被工具权限拒绝。**92→90 调整、v2 历史与对比在真机标 BLOCKED**。
- 真机断网/超时重试：断网状态已建立（`adb reverse --list` 为空），但调整按钮未触发请求，因此未取得“错误提示→重试成功”的真机证据，标 BLOCKED；不把 JVM 覆盖写成真机通过。

## 已知问题/边界

- 摄影澄清页的“拍摄时如何稳定手机？”出现了“没有灶具”选项（既有 UI 选项问题，非 D5 新增）。
- 运镜 Canvas 为 2D 俯视/取景示意，不代表真实 3D 轨迹、焦距或景深；只渲染结构化 `CameraMoveSpec`。
- 真机截图未做 AI 视觉检查（当前会话模型不支持图片输入）；结论来自 UI 层级文本与服务端返回值/日志。
- 真机按钮在滚动容器底部存在点击命中不稳定的现象（播放/暂停、创建新版本均出现过），已通过多次/前后时间轴比对确认播放控制，但配方调整未能完成。
## 2026-11-07 confirmation_required 真机走查

- 设备：realme GT6 / RMX3800，adb 序列号 `eeffd16b`，`adb devices` 状态 `device`；`adb reverse --list` 含 `tcp:8000 tcp:8000`。
- 服务端：`GET http://127.0.0.1:8000/v1/health` → 200 `{"status":"ok","api_version":"v1","checks":{"store":true,"ffmpeg":true,"model_configured":true}}`（未停止/重启服务端）。
- APK：`android/app/build/outputs/apk/debug/app-debug.apk`，10,838,706 字节，2026-11-07 11:51:21（第 16 轮构建）。
- 场景会话：`sess_01M6P54DER9GF7SNX7ABT8GXBD`，唯一配方 `recipe_01M6P5BDZT9557YX026QWNS4R6`（v1，水 225 g / 粉 15 g / 92 °C / 150 秒，缺 `total_sources`）。

### API 基线复核（真机前置，只读）

- `GET /v1/sessions/<id>/recipes` → 200，仅 1 条：v1、`water_g=225.0`、无 `total_sources` 键；`GET /v1/recipes/<v1id>/history` → 200 `[1]`。
- `POST /v1/recipes/<v1id>/adjustments` `{"base_version":1,"variable":"water_g","to_value":240,"reason":"probe"}` → **422**，`details.reason=total_source_unconfirmed`、`confirmation_required=true`、`requires_final=true`、`candidates` 数量 **5**。
- 结论：**PASS**。证据：`work/probe_baseline.json`（脚本 `work/probe_baseline.py`）。

### 分项结论

| # | 分项 | 实际观察 | 结论 | 证据 |
|---|---|---|---|---|
| 1 | 安装/启动 | `adb install -r` → `Success`；`am force-stop` + `am start -n com.tutorialcoach.app/.MainActivity` 后进入 V60 计划页（标题 “V60 pour over 15g coffee 225g water 92C 2m30s”、计划版本 v1、5 步）。`adb logcat -d` 8550 行中无 `FATAL EXCEPTION`/应用崩溃，仅 uiautomator 自身 `RuntimeInit` 日志。 | **PASS** | `work/device_confirm_step1_launch.xml`、`work/logcat_step1.txt` |
| 2 | 进入配方页 | 计划页滚到底 → 点「打开咖啡配方」→ 标题「咖啡配方」；参数区：咖啡粉 15 g、水 225 g、粉水比 1:15、水温 92 °C、研磨中细、总时长 150 秒；版本行 `v1 · V60 · pour_over · 1 份`。 | **PASS** | `work/device_confirm_step2_recipe_page.xml`、`work/device_confirm_step2_scrolled.xml` |
| 3 | 触发确认弹窗 | 单变量调整区选中 `water_g`，新值输入 240、原因 `final-check`，点「创建新版本（单变量）」→ 出现「确认总水量来源」弹窗。 | **PASS** | `work/device_confirm_step3_dialog.xml`、`work/device_confirm_step7_dialog.xml` |
| 3b | 候选原文片段 | 弹窗 5 行候选均含原文片段：步骤1「固定演示参数：咖啡粉 15 g，水 225 g，水温 92 °C，总时长 150 秒」；步骤3「目标在约 150 秒时累计注水至 225 g，并在该时间点前后结束注水」；步骤3「全程固定参数：咖啡粉 15 g，水 225 g，水温 92 °C，总时长 150 秒」；步骤3「若流速偏快，可先注水至 210 g 再继续」；步骤5「注水至 225 g，等待滤杯内液体滴完」。 | **PASS** | `work/device_confirm_step3_dialog.xml`、`work/screen_step4_error.png` |
| 4 | 缺项提示（勾「总量」不勾「最终」） | 仅勾第一行「总量」后点「确认并重试」：弹窗保持打开、未写入（API 仍仅 v1，`server/data/adjustments` 无该配方目录）；但「请选择最终执行指令。」**在弹窗打开期间不可见**（UI dump 与截图均无该文本），关闭弹窗后才在页面顶部 ErrorBanner 显示「出错了 / 请选择最终执行指令。」。原因：`state.error` 的 ErrorBanner 渲染在页面 Column（`RecipeScreen.kt:98-105`），被 `WaterSourceConfirmationDialog` 的 AlertDialog（`RecipeScreen.kt:331-379`，`AlertDialog` 起于 338）覆盖；校验本身在 `RecipeViewModel.kt:348-350` 设置 error 后直接 return（未发请求）。 | **BLOCKED（缺陷）**：逻辑正确，但预期“界面显示错误文案且弹窗仍在”未达成 | `work/device_confirm_step4_total_only.xml`、`work/device_confirm_step4_error2.xml`、`work/screen_step4_error.png`、`work/device_confirm_step5_top.xml` |
| 5 | 取消不写入 | 点「取消」→ 弹窗关闭；`GET /v1/sessions/<id>/recipes` → 仅 v1（225.0，无 `total_sources`）；`server/data/recipes/sess_.../` 仅 `recipe_01M6P5BDZT9557YX026QWNS4R6.json`；`server/data/adjustments` 无新增。 | **PASS** | `work/device_confirm_step5_after_cancel.xml`、`work/probe_baseline.json` |
| 6 | 版本冲突 | 弹窗打开状态下用 API 建 v2（`base_version=1`、`declaration=[0,2]`、`final=[4]`）→ **201**，`recipe_01M6T2HG72KP47MT1VBDV9QNE8`（240 g / 1:16）；设备勾选行1「总量」+ 行5「最终」后点「确认并重试」→ 客户端显示「出错了 / 配方版本已变化，已刷新最新版本；请重新调整。」，页面刷新到 `v2 · 水 240 g · 粉水比 1:16`。 | **PASS** | `work/device_confirm_step6_top.xml`、`work/screen_step6_conflict.png`、`work/conflict_v2.json` |
| 7 | 确认成功（v2） | 用 `os.remove` 删除第 6 步实验 v2 配方与 adjustment（仅这两类文件，v1 未改动）→ API 复核回到仅 v1（history `[1]`）；force-stop 重启 → 配方页显示 v1（225 g / 1:15）；重填 240 + 原因，勾行1「总量」+ 行5「最终」→ 确认成功：界面「已创建 v2，只调整了 water_g。」、`v2 · V60 · pour_over · 1 份`、咖啡粉 15 g / 水 240 g / 粉水比 1:16 / 92 °C / 中细 / 150 秒；API `recipes` = v1(225.0, 1:15, 无 `total_sources`) + v2(240.0, 1:16, 有 `total_sources`)，`history` = `[(1,225,15),(2,240,16)]`。 | **PASS** | `work/device_confirm_step7_result.xml`、`work/screen_step7_success.png`、`work/device_confirm_step7_checked.xml` |

### 最终服务端状态

- v1 `recipe_01M6P5BDZT9557YX026QWNS4R6`：`version=1`、`water_g=225.0`、`ratio=15.0`，**文件内无 `total_sources`**（保持旧配方原状，未被“修复”）。
- v2 `recipe_01M6T2Y5M56ZFFTECNSNQRCX5V`：`version=2`、`water_g=240.0`、`ratio=16.0`，含 `total_sources`；adjustment `adj_01M6T2Y5M5NXQP4NH7HV360342`。
- 第 6 步冲突实验版本（`recipe_01M6T2HG72KP47MT1VBDV9QNE8` / `adj_01M6T2HG73CGPP5MSPYXZV5GRW`）已清理，最终状态可解释。

### 环境干扰与未完成项

- 环境干扰（非应用缺陷）：走查步骤 7 期间，外部应用（`com.hypergryph.arknights`）抢占前台导致 tutorialcoach 进程被杀，重新启动后 `restore()` 一度失败显示首页；再次 force-stop/start 后成功恢复 `last_session_id` 并进入计划页。未清空应用数据、未修改客户端代码或测试。
- 未完成项：分项 4「缺项提示可见性」未达成（错误文案被弹窗遮挡），已按缺陷记录，需客户端调整 Dialog 内错误展示后复测；其余 7 项真机走查完成。
- 截图未做 AI 视觉复核，结论来自 UI 层级文本、截图人工比对与服务端 API/文件状态。
### 任务#2（旧配方场景 API 验收）完成度

- 已执行并通过：场景构造复核（仅 v1、`water_g=225.0`、无 `total_sources`）；`confirmation_required` 422（`requires_final=true`、5 个含原文片段候选）；完整确认 **201**（步骤 6 的 `POST /adjustments` 返回 201 并生成 v2 240 g / 1:16；步骤 7 真机同样确认成功）。
- 补充 API 校验（本轮补跑，脚本 `work/probe_confirm_invalid.py`，结果 `work/probe_confirm_invalid2.json`）：
  - **缺 final 完整性 422**：`declaration=[0]`、`final=[]` → 422 `invalid_water_source_confirmation`，`missing=["final"]`、`requires_final=true`、`created=null`。
  - **非法 final 422**：`final=[3]`（210 g，值不等于总量 225 g）→ 422，`invalid=[3]`、`created=null`。
  - **非法 declaration 422**：`declaration=[3]` → 422，`invalid=[3]`、`created=null`。
  - 三例执行后 `versions_after` 仍仅 `v1[225]`（未写入）；随后恢复 v2 成功，`versions_restored = v1[225] + v2[240]`。
- 说明：早期假设版本的脚本结果 `work/probe_confirm_invalid.json` 中曾出现“declaration 201 / final 409”，原因是脚本把 terminal 当 declaration 的角色假设过严（契约只要求 `final` 必须 terminal 且值匹配总量；terminal 作 declaration 属允许），**不是产品缺陷**；该用例当时多写的一个 v2 已清理，最终状态见上“最终服务端状态”。
- 说明：任务#2 原文的“验证后清理 v2 复原为仅 v1”服务于真机前置状态；按任务#4 要求，最终状态保留 v1 与真机确认成功的 v2，未额外“修复” v1 的 `total_sources`。
## 2026-11-07 修复后真机复验（8001 独立验收数据）

本节记录 `ebcccb1` 之后两项修复（同值 explicit 声明同步 + 弹窗内错误展示）的真机复验，**不改写上文修复前结论**：修复前走查为 8 分项 **7 PASS / 1 BLOCKED**（分项 4 错误文案被 `AlertDialog` 遮挡）。

### 环境

- 设备：realme GT6 / RMX3800，adb 序列号 `eeffd16b`。
- APK：`android/app/build/outputs/apk/debug/app-debug.apk`，10,838,706 字节，mtime 2026-11-07 12:57:54，SHA-256 `f7894375db2f4fb95358c45b24e4f39614784681a28db255d6ece40cdc1e5bf9`；`adb install -r` → `Success`。
- 数据与服务端：8001 为独立验收数据（`TUTORIAL_DATA_DIR` 指向 `work/d5_accept_20261107`），`adb reverse tcp:8000 → tcp:8001`；`GET /v1/health` 返回 ok。8000 正式数据服务未停止/未重启，`server/data/` 未改动。
- 基线：仅 v1（225 g、无 `total_sources`）；调整返回 422 `total_source_unconfirmed`、候选 6 条。

### 12 分项实际观察

| # | 分项 | 实际观察 | 结论 |
|---|---|---|---|
| 1 | 启动/旧版参数 | force-stop 后启动进入 V60 计划页，滚动到底点「打开咖啡配方」→ 配方页 `v1 · V60 · pour_over · 1 份`，15 g / 225 g / 1:15 / 92 °C / 中细 / 150 秒。 | **PASS** |
| 2 | 触发弹窗 | `water_g` 改 240、原因 `acceptance` → 「确认总水量来源」弹窗，6 行候选（每行含「总量」「最终」复选框）。 | **PASS** |
| 3 | 缺项提示（C1/C2） | 只勾 candidate 0「总量」→「确认并重试」：弹窗保持，**弹窗内可见「请选择最终执行指令。」**；candidate 0 勾选保留；API 仍仅 v1、0 adjustments。 | **PASS** |
| 4 | 修正后清提示（C3） | 勾 candidate 4「最终」→ 弹窗内错误立即消失，两处勾选保留。 | **PASS** |
| 5 | 后端拒绝（C4） | 仅勾 c0「总量」+ c4「最终」→ 422 `water_total_conflicts_with_final`，弹窗内可见「计划的总水量 240 g 与最终停止条件 225 g 冲突；未创建或未调整配方。」；弹窗保持、c0/c4 勾选保留、无写入。 | **PASS** |
| 6 | 取消不写入（C5） | 点「取消」→ 弹窗关闭；API 仍仅 v1、无 adjustments。 | **PASS** |
| 7 | 版本冲突（C6） | 弹窗打开时 API 建 v2（201）→ 设备确认收到 409 `VERSION_CONFLICT`（`details.current_version=2`），弹窗关闭，页面「出错了 / 配方版本已变化，已刷新最新版本；请重新调整。」并刷新到 v2。 | **PASS** |
| 8 | 恢复 v1 | `os.remove` 仅删白名单两文件 → API 回 `[v1]`；force-stop 重启后显示 v1 225 g。 | **PASS** |
| 9 | 完整确认（C7） | 勾 c0「总量」+ c4/c5「最终」→ **201** 生成 v2 `recipe_01M6T6F479SE3R4QBZB5V27SJG`、adjustment `adj_01M6T6F479SHW67QA885X75FEW`；弹窗关闭，界面「已创建 v2，只调整了 water_g。」，水 240 g、1:16。 | **PASS** |
| 10 | 一致性与旧版原值 | v2 water 240 / ratio 16 / ingredients 水 240；step0 instruction 与 target 均「总水量 240 g」（只勾一处声明也同步）；step1 中途「注水至 100 g」保持（未选的「继续注水至 225」也保持原值）；step2 instruction/target 均「最后注水至 240 g 后停止」；`total_sources` 4 条 = 2 explicit declaration + 2 final；v1 仍 version1/225/文本 225/无 `total_sources`；history versions `[1,2]`。 | **PASS** |
| 11 | 真机配方对比 | 配方页「版本历史」+「对比最近两个版本」入口；点击后 `/compare` 200，**真机渲染**「对比 v1 → v2」+「water_g：225.0 → 240.0（Δ15.0）」+「ratio：15.0 → 16.0（Δ1.0）」+ 三条说明；未用 API compare 冒充。 | **PASS** |
| 12 | 收尾 | 保留 v1+v2（recipes 2 文件、adjustments 1 文件）；前台 `com.tutorialcoach.app`，未见外部应用抢占。 | **PASS** |

### C4 证据方式说明（不夸大）

- 分项 5 的 **422 响应体未单独持久化**；结论依据为服务端 `app.log` 记录 `adjustments 422`、弹窗内错误文案与验收数据目录无新增。**不表述为“已保存 422 响应体”**。
- 分项 7 的 409 响应体由同 body 的复现 POST 取得（仍 409、未产生新文件），见 `work/d5_fix_api_s7_409.json`。

### 证据路径（本地 `work/`，不提交）

- 记录：`work/d5_fix_device_evidence.md`
- API：`work/d5_fix_api_baseline.json`、`d5_fix_api_s3.json`、`d5_fix_api_s5.json`、`d5_fix_api_s6.json`、`d5_fix_api_s7_conflict_post.json`、`d5_fix_api_s7_409.json`、`d5_fix_api_final.json`、`d5_fix_api_postcheck.json`
- UI dump / 截图：`work/d5fix_s*.xml`、`work/d5fix_s*.png`
- 服务日志：`work/d5_accept_20261107/logs/app.log`

### 四项验收状态（分列）

| 验收项 | 状态 | 说明 |
|---|---|---|
| 真机确认流程（本轮） | **PASS** | 12 分项全部 PASS |
| 用户自拍环绕 | **BLOCKED** | 仍无用户自拍素材 |
| 真机配方对比 | **本轮 PASS** | 真机入口渲染 v1→v2 差异（之前轮次为 BLOCKED，本轮已达成） |
| 真机断网重试 | **BLOCKED** | 本轮未触发 |

### 最终数据状态（8001 验收数据）

- `work/d5_accept_20261107/recipes/sess_01M6P54DER9GF7SNX7ABT8GXBD/`：`recipe_01M6P5BDZT9557YX026QWNS4R6.json`（v1，225 g，无 `total_sources`）、`recipe_01M6T6F479SE3R4QBZB5V27SJG.json`（v2，240 g / 1:16）。
- `work/d5_accept_20261107/adjustments/recipe_01M6P5BDZT9557YX026QWNS4R6/`：`adj_01M6T6F479SHW67QA885X75FEW.json`。
- 冲突实验产生的 v2 已按白名单删除；`server/data/` 与 8000 服务未改动。
- 真机截图未做 AI 视觉复核；结论来自 UI 层级文本、人工截图比对与服务端 API/文件状态。