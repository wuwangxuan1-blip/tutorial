# 实现状态

> 最后更新：2026-11-05（P0/D1 + P1/D2 完成；P2/P3 复审修复已实现并完成真机复核，等待复审）
> 状态取值：未开始 / 进行中 / PASS / BLOCKED。PASS 只表示有本文件“证据”列指向的真实命令输出、日志或截图；未执行的项目不得写 PASS。

## 1. 需求到阶段映射

| 需求（CC_TASK / 产品规格） | 规格位置 | 阶段 | 状态 | 证据 |
|---|---|---|---|---|
| Android 可安装 APK，非 WebView/PWA | PRODUCT 2.1、AC-01；TECH 1/6 | D1 | **PASS（主流程）**：APK 构建/安装/启动成功；真机完成目标→澄清→真实计划→步骤卡；诊断、跨会话隔离、断网恢复通过 | `device_verification.md`、`android_apk_info.txt` |
| 四领域全部保留 | PRODUCT 5、AC-06 | D2–D6 | 未开始（D1 仅烹饪最小链路；领域枚举保留四值） | — |
| 目标为主入口，可附参考教程 | PRODUCT P-01/P-02、AC-15/16 | D1/D2/D6 | 进行中（目标入口实现；参考导入未开始） | — |
| 按领域追问条件，最多两轮 | PRODUCT P-03、AC-06 | D1/D2 | **PASS（D2 完整）**：两轮上限、可选跳过、真机两轮验证 | `server_pytest.log`、`device_verification.md` |
| 准备清单/步骤/时间/可观察完成标准 | PRODUCT P-04/P-05、AC-06 | D1/D2 | **PASS（D2 完整）**：真实计划含准备/假设/时间/标准/安全 | `vertical_flow.json`、`device_plan_cooking.json` |
| 步骤卡、随时提问、上一步/下一步、暂停、计时、保存/恢复 | PRODUCT P-05/P-06、AC-07/08 | D1/D2（只读）/D3 | D2 只读步骤卡真机验证（1/5→2/5）；计时/暂停/进度写入未开始 | `device_verification.md` |
| 修改条件与计划锁定 | PRODUCT P-05、AC-08/08b | D3 | 未开始（PLAN_LOCKED 服务端防护已写，D3 完整实现） | — |
| 照片/截图/短片反馈，带证据 | PRODUCT P-07、AC-09/10 | D4 | 未开始 | — |
| 摄影运镜结构化路径 + 动画 | PRODUCT 5.2/5.3、AC-11 | D4/D5 | 未开始 | — |
| 咖啡配方/口味/单变量/历史/对比 | PRODUCT P-10、AC-12 | D5 | 未开始 | — |
| 成果与记录可回查 | PRODUCT P-09、AC-18 | D3/D6 | 未开始 | — |
| 真实 DeepSeek 文本/图片/JSON，Key 仅服务端 | TECH 3.3、API 1.3、AC-03/04/05/14 | D1/D2 | **PASS**：文本/JSON/图片真实通过；D2 真实两轮计划 5 步；Key 不在响应/证据 | `model_probe.json`、`vertical_flow.json`、`secret_scan.json` |
| 视频抽帧、不分析音频 | API 3.8/7、AC-10 | D4 | 未开始 | — |
| 食物安全/口味边界 | PRODUCT 5.2、AC-09/12 | D4/D5 | D1 提示词/计划已含边界；媒体判断未开始 | `plan_cooking.txt` |
| 断网/超时/429/非法 JSON/媒体失败恢复 | PRODUCT 8、AC-13 | D1/D2/D6 全量 | **D2 PASS**：无 Key/429/超时/非法 JSON/结构失败/拒绝/一次修复/幂等/GET 恢复均有测试；媒体失败仍属 D4 | `server_pytest.log`、`error_paths.md` |
| 秘密/日志脱敏/不提交 .env | AC-14、STANDARDS 6 | D1 起持续 | PASS：扫描 111 文件无匹配；`.env` 被忽略 | `secret_scan.json` |
| 比赛材料与码道证据 | AC-20、COMPETITION_CHECKLIST | D7 | 未开始 | `codearts_proof/day1/` |

## 2. D1/P0 逐项状态

| P0 验收项 | 状态 | 证据/说明 |
|---|---|---|
| 1. `gradlew --version` = Gradle 8.9 + JVM 21.0.7 | **PASS** | `gradle_version.txt` |
| 2. `assembleDebug` 成功且 APK 存在 | **PASS** | 标准 Wrapper + JBR 21，强制重建 `BUILD SUCCESSFUL in 28s`，APK 约 10 MB，`aapt2` 核验通过 |
| 2b. 安装/启动 | **PASS（P0 场景）** | realme GT6（RMX3800/Android 16），`adb install -r` Success，冷启动成功 |
| 3. `/v1/health` 200、无 Key 泄露、诊断页显示状态 | **PASS** | 服务端 `health.json`；真机诊断页 `status=ok`、store/ffmpeg/model true、vision 探针通过 |
| 4. 创建会话按领域返回 3–5 问题或 `ready` | **PASS** | `session_create.json`（5 个问题）、`server_pytest.log`、真机澄清 5 问 |
| 5. 目标→澄清→真实模型计划→步骤卡 | **PASS（服务端 + 真机）** | 真机 5 步计划；模型 26.449 s / 4445 tokens；步骤卡 1/5→2/5 |
| 6. 文本/图片/JSON 探针真实结果 | **PASS**（三项均 ok） | `model_probe.json` |
| 7. 证据目录与状态更新 | **PASS** | `codearts_proof/day1/`、本文件 |
| 8. Git 本地提交/远程推送 | **PASS** | P0 功能 `bcd3cc9`、状态文档 `4798f2f`、第三轮修复 `f405461`、真机验证 `8a6365d`、D2 功能 `e268dfe`、P1 复审修复 `741b2e4` 均已推送；未强推；见 `git_status.txt`、`day2/git_status.txt` |

P0 结论：构建、服务端测试、安卓测试、真实模型探针、真机最小垂直流程均完成；剩余为未覆盖的健壮性与后续阶段能力，等待 Codex 复审后决定是否进入 P1/D2。

## 3. Codex P0 审查修复

审查报告：`docs/CODEX_P0_CODE_REVIEW.md`、`docs/CODEX_P0_CODE_REVIEW_ROUND2.md`、`docs/CODEX_P0_CODE_REVIEW_ROUND3.md`（Codex 产出，未修改其结论）。

| 项 | 状态 | 修复与验证 |
|---|---|---|
| 1. `ApiClient.execute` 缺 return，安卓编译失败 | 已修复并验证 | 改为 `return response.use { ... }`；第三轮 `testDebugUnitTest` 与 `assembleDebug` 均通过 |
| 2. plan-jobs 忽略 `Idempotency-Key` | 已修复并验证 | 服务端按 method+path+key 校验 body hash、replay 首次 202、冲突/处理中；新增 2 项单测；Android 复用同一逻辑请求的 key |
| 3. 过敏/器具数组字段被文本问题回答成字符串导致 422 | 已修复并验证 | 服务端对数组字段做显式分隔归一化（`无`→`[]`）；新增 2 项单测 |
| 4. 模型格式修复未 await | 现码已为 `await`（审查快照较早） | 新增修复路径单测（非法 JSON/结构失败/超时/拒绝）；P1 复审后服务端 47 项测试通过 |
| 5. 新建第二次练习可能显示上一份计划 | 已修复并真机验证 | `PlanScreen` 按 session id 作为 ViewModel key；`PlanViewModel` 监听 session 变化并取消旧轮询；`loadPlan` 仅在 session 匹配时更新；真机新建第二会话后计划页无旧计划 |
| 第二轮：Job 成功但 GET 计划失败后无法恢复 | 已修复并验证 | 保留“待取计划”状态；`retry()` 只重试 `GET /plan`，不重建 Job；取到计划后同步 session 版本；`PlanViewModelTest` 实际执行通过 |
| 第三轮：PlanViewModelTest 可空类型编译失败 | 已修复并验证 | `_session` 显式声明为 `MutableStateFlow<DomainSession?>`；完整安卓单测 12 项通过 |
| 第三轮：gradlew 依赖个人缓存/JDK 绝对路径 | 已修复并验证 | 生成标准 Wrapper（Gradle 8.9、官方 URL、SHA-256）；移除 `org.gradle.java.home`；README 说明 JDK/SDK/本地配置/首次构建 |

## 4. 剩余未验证项与边界（D2）

- **真机健壮性**：旋转、切后台、进程被杀后恢复未验证；D2 主流程/两轮澄清/步骤卡已通过。
- **中文输入**：设备端用 ASCII 目标自动化；中文目标已在服务端真实流程验证，中文输入法键盘未验证。
- **视觉检查**：截图仅本地保留，未做 AI 视觉检查；结论来自 UI 层级文本与服务端日志。
- **干净机器构建**：标准 Wrapper 已配置官方 URL/SHA-256；无缓存机器首次下载 Gradle/Maven 依赖未实测。
- **后续阶段**：计时/暂停/进度、媒体反馈、运镜、配方、参考教程（D3–D6）未实现，不能当作 D2 范围缺陷。
- **Git**：本阶段提交待推送，结果以实际命令为准。

## 5. 下一步

1. Codex 复审 P1/D2（含契约、错误路径与真机证据）。
2. 可选补测旋转/切后台/进程恢复、中文输入法、干净机器首次构建。
3. 推送本阶段提交；网络失败时如实记录。
4. 复审通过后再进入 P2/D3；不自动推进。

## 6. P1/D2 状态（2026-11-05）

| D2 验收项 | 状态 | 证据 |
|---|---|---|
| 契约样例 + 双端解析 | **PASS**：7 个 JSON 样例；服务端 8 项、安卓 6 项 | `contracts/`、`contract_validation.md` |
| 完整 Pydantic 校验 | **PASS**：Conditions/Question/Session/Plan/Step/Job/Error；非法枚举/空值/空标准拒绝 | `server_pytest.log` |
| 两轮澄清与可选跳过 | **PASS**：服务端测试 + 真机两轮；可选跳过不阻塞 ready | `server_pytest.log`、`device_verification.md` |
| 真实模型烹饪计划 | **PASS**：中文目标两轮 → 5 步、8 条假设、30.837 s/5196 tokens、stage=done | `vertical_flow.json` |
| 计划总览字段 | **PASS**：准备清单、假设、预计时间、步骤标准、安全提示；真机显示 6 条假设 | `plan_cooking_real.json`、`device_plan_cooking.json` |
| 步骤卡 | **PASS**：真机 1/5→2/5，完成标准/安全提示可见 | `device_verification.md` |
| 异常与恢复 | **PASS**：无 Key/429/超时/非法 JSON/结构失败/拒绝/一次修复/幂等/GET 重试 | `error_paths.md` |
| 安卓测试与 APK | **PASS**：21 项、0 失败；APK 构建成功约 11 MB | `android_test_results.txt`、`android_apk_info.txt` |
| `gradlew` 100755 | **PASS**：`git ls-files -s` = 100755 | `commands.md` |
| 真正模型 vs 替身 | 已区分：真实模型仅成功流程；失败路径用 MockTransport/假模型 | `error_paths.md` |

D2 结论：契约固化、完整烹饪文本流程、异常恢复与真机复测完成；等待 Codex 复审，不进入 P2/D3。
## 7. P1 复审修复（2026-11-05）

| 修复项 | 状态 | 验证 |
|---|---|---|
| 模型限流等待 | **PASS（JVM 测试替身）** | `PlanUiState.RateLimited` 显示 7 秒倒计时；等待期间 generate/retry 与 ViewModel 双重拦截；切换会话清理；`PlanViewModelTest` 2 项新增测试通过；未真机注入 429 |
| 两次非法 JSON 后 Job retryable | **PASS** | 真实 `ModelClient` + `httpx.MockTransport` 连续两次非法 JSON；Job `MODEL_BAD_OUTPUT` + `retryable=true`；调用次数恰好 2；无真实模型调用 |
| 过敏提示泛化 | **PASS** | 未提供过敏信息时提示“核对本次实际使用的食材和调味料”，不含番茄/鸡蛋/面条；`allergies=[]` 不生成该提示；蘑菇汤假模型测试通过；服务端真实计划已重跑（30.837 s/5196 tokens、8 条假设）；未真机重跑该计划 |

测试与构建：服务端 **47 passed**；安卓 **21 passed**（0 失败）；`assembleDebug` 成功，APK 约 11 MB。测试替身与真实模型严格区分；真机未重新验证限流 UI 与过敏提示（P2/P3 轮真机复核见第 8 节）。

## 8. P2/P3 复审修复（2026-11-05）

基线：`a486b65`。本轮只处理以下两项复审缺陷，不进入 P2/D3。

| 修复项 | 状态 | 验证 |
|---|---|---|
| P2 过敏提示槽位 | **PASS** | `plan_service.py` 为“未提供过敏信息”的通用提示预留 1 个槽位；模型返回 10 条假设时保留前 9 条原序，第 10 条为通用提示；`assumptions` 始终 ≤10；`allergies=[]` 仍不添加该提示。新增 `test_allergy_note_reserves_slot_when_model_returns_ten`，保留蘑菇汤通用文案与显式无过敏测试 |
| P3 共享限流冷却 | **PASS** | `RateLimitGate` 由 `AppContainer` 持有，`PlanScreen` 按 session id 创建 ViewModel 时共享同一 Gate；冷却期 `generate()`/`retry()` 均被拦截，不调用 `createPlanJob`；切会话取消旧任务并重置为 Idle/Ready，但保留剩余冷却；页面显示剩余秒数、生成按钮禁用、错误区重试按钮隐藏。`PlanViewModelTest` 覆盖 7 秒→3 秒→约 4 秒、冷却内重复触发不增 Job、结束后手动生成使用新会话 ID |
| P0 回归 | **PASS** | 计划已生成、首次 GET 失败、重试只 GET 原计划：`createCalls` 不增，`loadCalls` 增加 |

测试与构建（本轮实测）：

- 服务端 **48 passed**，0 失败：`test_contract_examples` 8、`test_health` 3、`test_idempotency` 5、`test_model_client_errors` 8、`test_plan_assumptions` 3、`test_plan_flow` 6、`test_plan_repair` 6、`test_sessions` 9。
- 安卓 `testDebugUnitTest --rerun-tasks` **21 passed**（本项修复后重跑为 **23 passed**，见本节末），0 失败：`ContractExamplesTest` 6、`DtoTest` 3、`ErrorMapperTest` 5、`PlanValidatorTest` 4、`PlanViewModelTest` 3。
- `assembleDebug` BUILD SUCCESSFUL；APK `android/app/build/outputs/apk/debug/app-debug.apk`，10,445,372 字节（约 10.4 MB）。
- `git diff --check` 通过；`git ls-files -s android/gradlew` 为 `100755`。

真机复核（2026-11-05，realme GT6 / RMX3800 / Android 16，adb `eeffd16b`）：

- 使用“真实服务端代码 + 测试模型替身”（`work/device_review_test_server.py`）注入 `MODEL_RATE_LIMITED` 与 10 条假设；**不是真实 DeepSeek 输出**。
- 7 秒限流：页面显示倒计时；冷却内重复点击生成，Job 数不变（15→15）；冷却结束后手动生成，Job 15→16。
- 切会话：20 秒注入下，新会话保留剩余冷却、保持“条件已就绪”、无旧错误覆盖；冷却内点击不新建 Job（17→17）；冷却结束后使用新会话生成成功（17→18）。
- 10 条假设：计划页显示“模型假设 1–9”原序 + 第 10 条通用过敏提示，共 10 条，通用提示恰好一次。
- 后续修复（2026-11-05）：限流冷却改为单调时钟截止时间（生产 `SystemClock.elapsedRealtime()`，测试注入时钟）；剩余秒数按“截止时间 − 当前时间”向上取整，`isBlocked()` 直接比较截止时间，刷新协程只负责显示，设备休眠/调度延迟不再延长实际冷却。新增 `RateLimitGateTest` 2 项；安卓本轮 **23 passed**（0 失败：原 21 项 + `RateLimitGateTest` 2 项），`assembleDebug` 成功，APK 10,445,372 字节。

仍未验证（不得当作已通过）：真实 DeepSeek 恰好触发 429 并返回 `retry_after_s`、真实模型一次返回 10 条假设、旋转/切后台/进程被杀恢复、中文输入法直接输入目标、截图 AI 视觉检查。详细记录见 `codearts_proof/day2/review_fix_device.md`。
