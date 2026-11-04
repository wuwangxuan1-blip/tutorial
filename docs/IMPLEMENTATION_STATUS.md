# 实现状态

> 最后更新：2026-11-04（P0/D1，含 Codex 审查修复）
> 状态取值：未开始 / 进行中 / PASS / BLOCKED。PASS 只表示有本文件“证据”列指向的真实命令输出、日志或截图；未执行的项目不得写 PASS。

## 1. 需求到阶段映射

| 需求（CC_TASK / 产品规格） | 规格位置 | 阶段 | 状态 | 证据 |
|---|---|---|---|---|
| Android 可安装 APK，非 WebView/PWA | PRODUCT 2.1、AC-01；TECH 1/6 | D1 | 进行中：Codex 复审环境已构建 APK（旧源码）；码道沙箱无法执行构建，P2 修复后需重建；设备安装 BLOCKED | `codearts_proof/day1/build_status.md`、`android_apk_info.txt` |
| 四领域全部保留 | PRODUCT 5、AC-06 | D2–D6 | 未开始（D1 仅烹饪最小链路；领域枚举保留四值） | — |
| 目标为主入口，可附参考教程 | PRODUCT P-01/P-02、AC-15/16 | D1/D2/D6 | 进行中（目标入口实现；参考导入未开始） | — |
| 按领域追问条件，最多两轮 | PRODUCT P-03、AC-06 | D1/D2 | PASS（烹饪规则问题库 + 两轮上限；单测覆盖） | `server_pytest.log` |
| 准备清单/步骤/时间/可观察完成标准 | PRODUCT P-04/P-05、AC-06 | D1/D2 | PASS（真实模型计划，Pydantic 校验） | `vertical_flow.json` |
| 步骤卡、随时提问、上一步/下一步、暂停、计时、保存/恢复 | PRODUCT P-05/P-06、AC-07/08 | D1（只读步骤卡）/D3 | D1 只读步骤卡已实现；设备 UI 未验证；计时/暂停/进度写入未开始 | `StepScreen.kt` |
| 修改条件与计划锁定 | PRODUCT P-05、AC-08/08b | D3 | 未开始（PLAN_LOCKED 服务端防护已写，D3 完整实现） | — |
| 照片/截图/短片反馈，带证据 | PRODUCT P-07、AC-09/10 | D4 | 未开始 | — |
| 摄影运镜结构化路径 + 动画 | PRODUCT 5.2/5.3、AC-11 | D4/D5 | 未开始 | — |
| 咖啡配方/口味/单变量/历史/对比 | PRODUCT P-10、AC-12 | D5 | 未开始 | — |
| 成果与记录可回查 | PRODUCT P-09、AC-18 | D3/D6 | 未开始 | — |
| 真实 DeepSeek 文本/图片/JSON，Key 仅服务端 | TECH 3.3、API 1.3、AC-03/04/05/14 | D1 | **PASS**：文本/JSON/图片均真实通过；Key 不在响应/证据 | `model_probe.json`、`secret_scan.json` |
| 视频抽帧、不分析音频 | API 3.8/7、AC-10 | D4 | 未开始 | — |
| 食物安全/口味边界 | PRODUCT 5.2、AC-09/12 | D4/D5 | D1 提示词/计划已含边界；媒体判断未开始 | `plan_cooking.txt` |
| 断网/超时/429/非法 JSON/媒体失败恢复 | PRODUCT 8、AC-13 | D1 部分/D6 全量 | D1 错误信封、模型错误映射、Job 失败态已实现；故障注入未做 | `server_pytest.log` |
| 秘密/日志脱敏/不提交 .env | AC-14、STANDARDS 6 | D1 起持续 | PASS：扫描 111 文件无匹配；`.env` 被忽略 | `secret_scan.json` |
| 比赛材料与码道证据 | AC-20、COMPETITION_CHECKLIST | D7 | 未开始 | `codearts_proof/day1/` |

## 2. D1/P0 逐项状态

| P0 验收项 | 状态 | 证据/说明 |
|---|---|---|
| 1. `gradlew --version` = Gradle 8.9 + JVM 21.0.7 | **PASS** | `gradle_version.txt` |
| 2. `assembleDebug` 成功且 APK 存在 | PASS（Codex 15:58Z，旧源码）；最终源码待复建 | `BUILD SUCCESSFUL in 27s`，APK 约 10 MB，`aapt2` 核验通过；随后 P2 修复未再构建 |
| 2b. 安装/启动 | **BLOCKED** | `adb devices` 为空；无 AVD；镜像仅残留 |
| 3. `/v1/health` 200、无 Key 泄露、诊断页显示状态 | 服务端 **PASS**；Android 设备 UI **BLOCKED** | `health.json`、`server_app_final.log` |
| 4. 创建会话按领域返回 3–5 问题或 `ready` | **PASS** | `session_create.json`（5 个问题）、`server_pytest.log` |
| 5. 目标→澄清→真实模型计划→步骤卡 | 服务端 **PASS**（4 步真实计划）；Android 设备 **BLOCKED** | `vertical_flow.json`、`vertical_flow.log` |
| 6. 文本/图片/JSON 探针真实结果 | **PASS**（三项均 ok） | `model_probe.json` |
| 7. 证据目录与状态更新 | **PASS** | `codearts_proof/day1/`、本文件 |
| 8. Git 本地提交/远程推送 | 待提交/推送 | `git_status.txt` |

## 3. Codex P0 审查修复

审查报告：`docs/CODEX_P0_CODE_REVIEW.md`（Codex 产出，未修改其结论）。

| 项 | 状态 | 修复与验证 |
|---|---|---|
| 1. `ApiClient.execute` 缺 return，安卓编译失败 | 已修复，待复编译 | 改为 `return response.use { ... }`；本会话无法复跑 `assembleDebug`，需复审/用户终端验证 |
| 2. plan-jobs 忽略 `Idempotency-Key` | 已修复 | 服务端按 method+path+key 校验 body hash、replay 首次 202、冲突/处理中；新增 2 项单测；Android 复用同一逻辑请求的 key |
| 3. 过敏/器具数组字段被文本问题回答成字符串导致 422 | 已修复 | 服务端对数组字段做显式分隔归一化（`无`→`[]`）；新增 2 项单测 |
| 4. 模型格式修复未 await | 现码已为 `await`（审查快照较早） | 新增 3 项修复路径单测：首次非法→修复成功、两次非法、修复超时 |
| 5. 新建第二次练习可能显示上一份计划 | 已修复（静态） | `PlanScreen` 按 session id 作为 ViewModel key；`PlanViewModel` 监听 session 变化并取消旧轮询；`loadPlan` 仅在 session 匹配时更新；设备 UI 未验证 |
| 第二轮：Job 成功但 GET 计划失败后无法恢复 | 已修复，待复测 | 保留“待取计划”状态；`retry()` 只重试 `GET /plan`，不重建 Job；取到计划后同步 session 版本；新增 `PlanViewModelTest`（假网关模拟首次 GET 失败、第二次成功），尚未在新构建中执行 |

## 4. 已知阻塞与待用户批准

- **Android build/APK**：Codex 复审环境已成功构建并核验 APK（2026-11-04T15:58Z），但该构建早于 P2 恢复逻辑修复；当前源码需在普通终端重建。码道本会话沙箱无法执行 `assembleDebug`。
- **设备安装/启动/截图**：无真机、无 AVD、无可用系统镜像；需要用户连接真机或批准安装镜像。
- **GitHub 推送**：`git ls-remote` 被沙箱网络拦截；提交可本地完成，推送结果以实际命令为准，不伪造。
- **Android 编译验证**：Codex 审查发现的缺 return 已修，但本会话不能复编译；`testDebugUnitTest` 也未执行。

## 5. 下一步

1. 用户/Codex 在普通终端执行 `android\gradlew.bat --no-daemon :app:testDebugUnitTest :app:assembleDebug`，确认新增的 `PlanViewModelTest` 与 APK。
2. 若通过，安装到真机走通“目标→澄清→真实计划→步骤卡”；无设备则保持 BLOCKED。
3. 推送本地提交（网络可用时）。
4. 复审 P0 后，再决定是否进入 P1/D2；不自动进入。