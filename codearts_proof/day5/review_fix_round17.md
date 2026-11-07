# D5 confirmation 修复与真机复验（第 17 轮）

基线：`ebcccb1`（上一轮文档/状态提交）。本轮修两项确认流程缺陷并做修复后真机复验，未进入 D6。

## 1. 同值显式总量声明一并更新 + 写入前整份配方校验

- 用户只确认一处总量声明时，同值 `explicit` 声明（`总水量`/`总注水`/`注水总量`/`总水`/`总量`/`总计`/`合计`/`最终注水`/`最终水量`）一并更新，不再只改被勾选的那一处。
- 写入前对改写后的整份配方重新定位并校验：总量唯一、最终停止条件一致；遗漏最终条件造成冲突时返回 **422**，旧版本保持原值。
- 回归：v2 的 step0 `instruction` 与 `target` 均为「总水量 240 g」（本轮只勾选 candidate 0 一处声明）；step1 中途「注水至 100 g」保持；step2 最终「最后注水至 240 g 后停止」一致；v1 三处文本仍为 225。

## 2. Android 确认弹窗内的错误展示与交互态

- 错误提示渲染在同一 `AlertDialog` 内部，不再被弹窗遮挡。
- 修改任一勾选即清除旧错误；提交期间 `loading=true` 禁用勾选/确认/取消；取消/成功时清错误。

## 3. 改动文件（5 个，工作区未提交 → 本轮提交 1）

| 文件 | 改动 |
|---|---|
| `server/app/services/recipe_service.py` | 同值 explicit 声明合并更新；写入前整份配方重新定位/校验 |
| `server/tests/test_recipe.py` | 同值声明同步、冲突不写入、旧版原值回归 |
| `android/app/src/main/java/com/tutorialcoach/app/ui/screens/recipe/RecipeScreen.kt` | 错误移入 `AlertDialog` 内；勾选清除错误；loading 禁用交互 |
| `android/app/src/main/java/com/tutorialcoach/app/ui/screens/recipe/RecipeViewModel.kt` | 勾选/取消/成功清理错误；提交态 |
| `android/app/src/test/java/com/tutorialcoach/app/ui/screens/recipe/RecipeViewModelTest.kt` | 弹窗内错误、清错误、loading 回归 |

## 4. 本轮实测

- 后端：`server/.venv/Scripts/python.exe -m pytest -o addopts="" -q` → **138 passed / 0 failed**（18.60 s）；`tests/test_recipe.py` → **32 passed**（5.69 s）。日志 `work/d5_fix_pytest_full.log`、`work/d5_fix_pytest_recipe.log`，汇总 `work/d5_fix_pytest.txt`。
- Android：清空 `test-results` 后 `:app:testDebugUnitTest --rerun-tasks`（会话级 `JAVA_HOME=D:/Java/ideaIU-2025.2.win/jbr`，JBR 21）→ BUILD SUCCESSFUL（28 s，22 tasks）；**60 tests / 0 failures / 0 errors**（14 套件，`RecipeViewModelTest` 9 含新回归）。日志 `work/d5_fix_android_tests.log`，汇总 `work/d5_fix_android_tests.txt`。
- `:app:assembleDebug --rerun-tasks` → BUILD SUCCESSFUL（26 s，35 tasks）；APK `android/app/build/outputs/apk/debug/app-debug.apk` **10,838,706 字节**，mtime **2026-11-07 12:57:54**（晚于最后修改源码 `RecipeScreen.kt` 的 12:38:22），SHA-256 `f7894375db2f4fb95358c45b24e4f39614784681a28db255d6ece40cdc1e5bf9`。日志 `work/d5_fix_apk.log`，汇总 `work/d5_fix_apk.txt`。
- 密钥扫描：提交前重跑 `server/.venv/Scripts/python.exe scripts/scan_secrets.py`，结果见 `secret_scan.json`（以本轮实际输出为准）。

## 5. 真机复验（realme GT6 / RMX3800 / `eeffd16b`，8001 独立验收数据）

- 环境：新 APK `install -r` → `Success`；`adb reverse tcp:8000 → tcp:8001`；`/v1/health` ok；基线仅 v1（225 g、无 `total_sources`），调整返回 422 `total_source_unconfirmed`、候选 6 条。8000 正式数据服务未停止/未重启，`server/data/` 未改动。
- 12 个分项全部 **PASS**：启动/旧版参数、触发弹窗、弹窗内缺项提示（保留勾选、无写入）、改选后清提示、后端 422 拒绝时弹窗内错误且保留选择、取消不写入、409 版本冲突并刷新、恢复 v1、完整确认 201 生成 v2、v2 一致性与 v1 原值、真机「对比最近两个版本」渲染 v1→v2、收尾保留 v1+v2。
- C4（后端拒绝）的 422 响应体未单独持久化；依据为服务端 `app.log` 的 422、弹窗内错误文案与数据目录无新增，不将其表述为“响应体已保存”。
- 真机对比为真机入口点击后渲染结果（`/compare` 200 + 页面文本），未用 API compare 输出冒充。

## 6. 四项验收状态（分列，不合并）

| 验收项 | 状态 | 依据 |
|---|---|---|
| 真机确认流程（本轮） | **PASS** | 12 分项，含弹窗内错误可见、改选清提示、取消不写入、后端拒绝保留选择、409 刷新、201 v2、真机对比 |
| 用户自拍环绕 | **BLOCKED** | 仍无用户自拍素材 |
| 真机配方对比 | **本轮 PASS** | 真机「对比最近两个版本」入口渲染 v1→v2 差异（water_g 225→240 Δ15；ratio 15→16 Δ1） |
| 真机断网重试 | **BLOCKED** | 本轮未触发 |

## 7. 证据路径（本地 `work/`，按规则不提交）

- 真机记录：`work/d5_fix_device_evidence.md`
- API 快照：`work/d5_fix_api_baseline.json`、`work/d5_fix_api_s3.json`、`work/d5_fix_api_s5.json`、`work/d5_fix_api_s6.json`、`work/d5_fix_api_s7_conflict_post.json`、`work/d5_fix_api_s7_409.json`、`work/d5_fix_api_final.json`、`work/d5_fix_api_postcheck.json`
- UI dump：`work/d5fix_s*.xml`；截图：`work/d5fix_s*.png`
- 脚本：`work/d5_fix_api_check.py`、`work/d5_fix_api_adjust.py`、`work/d5_fix_restore_v1.py`、`work/ui_dump_parse.py`

## 8. 边界

- 未修改任何源码/测试之外的既有改动，未进入 D6。
- 真机截图未做 AI 视觉复核；结论来自 UI 层级文本、人工截图比对与服务端 API/文件状态。