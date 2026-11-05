# 实现状态

> 最后更新：2026-11-05（P0/D1、P1/D2、P2/P3；P2/D3 实现与真机验证完成，D3 复审缺陷已修复（三轮），等待复审）
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
## 9. P2/D3 实现（2026-11-05）

基线：`ab3fbfa`。本轮只实现 D3，不进入 D4。

### 服务端

| 能力 | 状态 | 说明 |
|---|---|---|
| `PATCH /v1/sessions/{id}/progress` | **PASS** | 合并更新；`ready→in_progress`；完成写 `self_reported`；非法状态转移拒绝；`base_plan_version` 冲突 409；计时器 anchor/step 校验 |
| pause / resume / complete / abandon | **PASS** | 暂停后进度写入返回 409 `SESSION_PAUSED`；完成只记 `user_reported`，不自动把剩余步骤标 done |
| `PATCH /v1/sessions/{id}/conditions` | **PASS** | 省略保持、null 清空非关键、空字符串 422、关键字段 null 原子失败；返回 `requires_regeneration`/`requires_revision` |
| `POST /plan-jobs` 计划锁定 | **PASS** | 有任意进度/当前步骤/计时器 → 409 `PLAN_LOCKED`；Job 写盘前二次检查版本与进度 |
| `POST /ask` | **PASS** | 步骤上下文、版本校验、45s 模型/60s 端点超时、坏输出 502、超时 504 |
| revision-jobs / apply / reject | **PASS** | 条件驱动修订；只改未完成步骤；涉及 done/skipped → 409 `STEP_LOCKED`；应用版本 +1、旧版本保留；拒绝幂等保护 |
| 软件领域计划 | **PASS** | `plan_software.txt`、软件澄清、备份/操作/完成检查；命令仅文本，不自动执行 |

服务端测试 **71 passed**（D3 新增 23 项：progress 5、conditions 7、revisions 5、ask 3、plan_software 3）。

### Android

| 能力 | 状态 | 说明 |
|---|---|---|
| 步骤卡前进/后退/完成/跳过 | **PASS** | 下一页/上一步同步 `current_step_id`；完成写 done + self_reported；跳过写 skipped |
| 计时/暂停/恢复 | **PASS** | `TimerEngine` 使用单调时钟锚点；剩余秒数不为负；暂停/恢复保持剩余时间 |
| 本地恢复/杀进程恢复 | **PASS** | `LocalStore` 保存会话/步骤/计时；App 启动调用 `restore()`；真机 force-stop 后恢复计划 v2、第 2 步与运行中计时 |
| 设备重启锚点确认 | 实现，JVM 验证 | 锚点失效时暂停并显示“继续/重置”确认；本轮未重启真机 |
| 提问面板 | **PASS** | 步骤上下文、回答/引用/局限；真机真实模型回答通过 |
| 条件修改页 | **PASS** | 条件 PATCH、impact 展示、有进度时引导修订 |
| 修订提案 | **PASS** | 列表、前后差异、应用/拒绝；真机真实模型一次应用、一次拒绝 |
| 软件领域端到端 | **PASS** | 真机真实模型 5 步计划，含备份与完成检查 |
| 离线/错误横幅 | **PASS（基础）** | 暂停写入、网络失败等显示明确错误 |

安卓测试 **28 passed**（D3 新增 TimerEngine 3、StepViewModel 2）；`assembleDebug` 成功；APK `android/app/build/outputs/apk/debug/app-debug.apk`，10,614,533 字节。

### 真机验证（2026-11-05）

- 设备 realme GT6 / RMX3800 / Android 16，adb `eeffd16b`；APK 安装 Success。
- 软件主线：真实 DeepSeek 生成 5 步计划（v1），含备份、复制、按日期重命名、核对、保留备份。
- 步骤：1/5 → 2/5 → 1/5；计时 5:00 → 4:56 → 暂停 → 继续 4:43；完成第 1 步后服务端记录 `step_1=done` + `self_reported`。
- 提问：第 2 步真实模型回答通过。
- 暂停/恢复：暂停后保存进度返回 409 `SESSION_PAUSED`，恢复后可继续。
- 条件修改：notes PATCH → `requires_revision=true`；真实模型生成修订（step_2/3/4），应用后计划 v2，`step_1` 内容与进度保持不变；第二个修订拒绝成功。
- 杀进程恢复：force-stop 重启后恢复计划 v2、第 2 步、计时 4:10。
- 服务端检查：同一会话 `POST /plan-jobs`（base=2）→ 409 `PLAN_LOCKED`。
- 真实烹饪回归（服务端 API，非设备 UI）：5 步番茄鸡蛋面，通用过敏提示存在。

详情：`codearts_proof/day3/device_verification.md`、`api_checks.md`、`server_pytest_summary.txt`、`android_test_results.txt`。

### 未验证 / 边界

- 设备重启后的计时确认弹窗：未重启设备；JVM `TimerEngineTest` 覆盖锚点失效。
- 旋转恢复：尝试修改设备旋转设置被权限拒绝，未执行。
- 中文输入法直接输入目标：设备自动化仅 ASCII。
- 截图 AI 视觉检查：结论来自 UI 层级文本与服务端 JSON/日志。
- 真实 DeepSeek 429 与一次 10 条假设：仍为 P2/P3 轮测试模型替身，记录在 `day2`。
- 媒体反馈、运镜、配方、参考教程属 D4+。


## 10. D3 复审修复（2026-11-05）

| 问题 | 修复 | 回归测试 |
|---|---|---|
| P1 修订可能写入无效计划 | `RevisionService.apply` 在任何写盘前构建完整候选计划并用 `PlanOut` 校验；失败返回 422 `INVALID_REQUEST` / `details.reason=revision_plan_invalid`，原计划、会话版本、进度和修订 `proposed` 状态均保留 | `test_revision_apply_rejects_remove_below_minimum`（3 步删 1）、`test_revision_apply_rejects_add_above_maximum`（15 步加 1）、`test_revision_apply_rejects_combined_removes_below_minimum`（组合删 2）；失败后 GET /plan 仍为原版本 |
| P2 补做/跳过前一步时覆盖下一步状态 | `completeStep()`/`skipStep()` 将当前步状态、自动前进、计时器变更合并为一次 PATCH；下一步仅在缺失/`not_started` 时标记 `in_progress`，已有 `done/skipped` 与证据保持不变；PATCH 失败时界面不提前前进 | `StepViewModelTest`：下一步已完成、下一步已跳过、PATCH 失败不前进；当前步仍写 `self_reported` |
| P3 重置已结束计时器后不刷新 | `resetTimer()` 成功后调用 `ensureTicker()`；`confirmTimerReset()` 复用 resetTimer；`ensureTicker()` 用 `ticker.isActive` 保证同一时刻只有一个刷新协程 | `StepViewModelTest`：计时自然结束→重置→推进时钟剩余秒数下降；无效锚点确认重置→推进时钟剩余秒数下降 |

本轮实测：服务端 **74 passed**；安卓 **33 passed / 0 failed**（StepViewModelTest 7 项）；`assembleDebug` BUILD SUCCESSFUL；APK 10,576,503 字节；`git diff --check` 通过；密钥扫描 223 文件、0 匹配、`clean=true`。真机本轮未重跑，待 Codex 复审后验证这三个修复路径。


## 11. D3 复审修复第二轮（2026-11-05）

| 问题 | 修复 | 回归测试 |
|---|---|---|
| P1 同一修订先 remove 再 update/reorder | `RevisionService._validate_changes` 增加顺序校验：按 changes 顺序维护可用步骤集合与剩余步数；被前序 remove 的步骤再被 update/reorder/remove 引用时返回 422 `INVALID_REQUEST` / `details.reason=step_removed_by_revision`。`apply` 使用顺序校验，且仍在校验完整候选计划后才写盘 | `test_revision_apply_rejects_update_of_removed_step`、`test_revision_apply_rejects_reorder_of_removed_step`：旧计划 v1/3 步不变、会话版本 1、进度保持、修订仍 `proposed`、`load_plan(session,2)` 为空 |
| P2 旧 finished PATCH 未返回时重置计时 | `StepViewModel` 增加 `timerEpoch` 与 `beginTimerChange()`：任何计时变更先递增 epoch 并取消旧 ticker；`ensureTicker()` 以 epoch 隔离旧协程，旧 finished PATCH 返回后不更新新计时状态 | `resetWhileFinishedPatchPendingKeepsNewCountdown`：用可挂起 fake 让 finished PATCH 挂起 → 重置 → 推进 5 秒新倒计时下降 → 释放旧响应 → 仍为新状态 → 再推进 2 秒继续下降 |

本轮实测：服务端 **76 passed / 0 failed**（test_revisions 增至 10 项）；安卓 **34 passed / 0 failed**（StepViewModelTest 增至 8 项）；`assembleDebug` BUILD SUCCESSFUL；APK 10,639,369 字节；`git diff --check` 通过；密钥扫描 226 文件、0 匹配、`clean=true`。真机未重跑；两项修复待 Codex 复审后补设备验证。


## 12. D3 复审修复第三轮（计时失败恢复，2026-11-05）

| 问题 | 修复 | 回归测试 |
|---|---|---|
| 计时 PATCH 失败后 ticker 已取消、倒计时停住 | `StepViewModel` 的 `runAction` 增加 `epoch` 参数：计时相关动作失败且 epoch 仍为当前时显示错误，并调用 `restoreTickerIfRunning()` 在计时器仍为 `running` 时重启刷新协程 | `completeStepPatchFailureShowsErrorAndKeepsCounting`：完成 PATCH 失败 → 显示错误、索引不前进、剩余秒数继续下降；`resetTimerPatchFailureKeepsOldRunningTimerCounting`：重置 PATCH 失败 → 旧 running 计时不被改成新计时，倒计时继续 |
| 旧请求失败干扰较新计时操作 | 失败路径仅在 `epoch == timerEpoch` 时显示错误、恢复 ticker、清除 saving；过期请求的失败静默丢弃 | `staleTimerFailureDoesNotAffectNewerTimerOperation`：旧重置失败请求挂起 → 新重置成功 → 释放旧失败 → 无错误、新计时保持并继续下降；旧的 finished PATCH 与重置交错回归保留 |

本轮实测：服务端 **76 passed / 0 failed**（未变）；安卓 **37 passed / 0 failed**（StepViewModelTest 11 项，新增 3 项）；`assembleDebug` BUILD SUCCESSFUL；APK 10,639,798 字节；`git diff --check` 通过。真机未重跑；失败恢复路径待复审后补设备验证。
