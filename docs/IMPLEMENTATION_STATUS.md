# 实现状态

> 最后更新：2026-11-05（D3 复审完成并推送；D4 媒体、反馈与摄影实现完成，等待 Codex 复审）
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


## 13. D4 媒体、图片/短片反馈与摄影（2026-11-05）

基线：`f5371c2`（D3 已推送，远端一致）。

### 服务端

| 能力 | 状态 | 说明 |
|---|---|---|
| `POST /v1/media` | **PASS** | multipart；JPEG/PNG/WebP 每张 ≤10 MiB；服务端转 JPEG、去 EXIF、长边 1024；HEIC 由 App 转 JPEG，服务端明确 415；视频 MP4/MOV ≤30s、≤100 MiB，ffprobe + 首帧解码校验 |
| `GET/DELETE /v1/media/{id}` | **PASS** | 元数据；被反馈引用时 409 `MEDIA_IN_USE` |
| feedback-jobs / feedback / list | **PASS** | 1–4 图或 1 视频、不可混用；`plan_version`/`step_id` 校验；Job 结果 `feedback_id`；证据必须属于本次媒体 |
| 图片反馈 | **PASS** | 每张图作为多图输入；观察引用 `media_id`；不推断内部温度/安全/口味；不自动完成步骤 |
| 视频反馈 | **PASS** | 1 fps 最多 8 帧、真实时间戳；证据校验 `frame_index` 与 `timestamp_s`；`audio_analyzed=false`；运动指标 10 fps/320px/最多 300 帧，`vidstabdetect` + `global_motions`，失败 `null` + limitation |
| 摄影领域 | **PASS** | 摄影提示词、已有摄影澄清问题；“手机环绕拍一杯咖啡 8 秒”真实计划 5 步；`visual_aid=null` 并明确提示；合法 `CameraMoveSpec` 保留，非法丢弃并提示 |
| 反馈不自动完成 | **PASS** | 反馈只把证据级改为 `model_observed`（无观察时保持 `media_submitted`），`step_statuses` 不变 |

本轮测试：服务端 **88 passed / 0 failed**（新增 `test_media` 4、`test_feedback` 5、`test_plan_photography` 3；原不支持领域测试改用 coffee）。

### Android

- Photo Picker 选择 1–4 张图片或 1 段短片（不申请存储权限）。
- 图片经 ImageDecoder/BitmapFactory 处理并压缩为 JPEG（长边 ≤2048、质量 85，HEIC 在系统支持时经 ImageDecoder 解码）；视频用 `MediaMetadataRetriever` 预检 ≤30 秒、≤100 MiB，超限直接提示、不上传。
- 隐私提示、证据缩略图、反馈页（评估、观察+媒体/帧时间戳、证据缩略图、不确定性、局限、运动指标、音频未分析、建议/追问）。
- 上传进度、分段重试（已上传媒体不重复上传）、Job 失败/视觉不可用明确原因；失败不生成假反馈。
- 反馈页当前不做自动完成、不做反馈驱动修订（修订仍走 D3 条件修订入口）。

本轮测试：Android **41 tests / 0 failed**（新增 `MediaLimitsTest` 2、`MediaViewModelTest` 2）；`assembleDebug` BUILD SUCCESSFUL；APK 10,783,309 字节。

### 视觉探针与真实素材

- 真实视觉探针：`codearts_proof/day4/vision_probe.json`；文本/JSON/视觉均 `ok`，64×64 橙色 PNG 返回“橙色”。
- 真实视觉 + 合成素材技术验证：`codearts_proof/day4/technical_synthetic_feedback.json`。
  - 合成咖啡杯示意图：反馈 `not_verified`，观察引用图片 media_id，明确说明是合成素材、不能替代现场验证。
  - 8 秒合成 testsrc 短片：8 个时间戳 0–7s，`audio_analyzed=false`，`motion_metrics` 非空（方法 `vidstabdetect_ascii_10fps_320px+global_motions`），模型明确识别为测试卡。
- **真实图片/真实短片反馈：BLOCKED**。仓库与 work 目录没有用户真实拍摄素材；没有用项目截图或合成素材冒充真实拍摄。详见 `codearts_proof/day4/real_material_blocked.md`。

### 未验证 / 边界

- 真实图片与真实短片各一次反馈：BLOCKED（缺素材）。
- 设备端 Photo Picker/上传/反馈页未真机走查（仅 JVM 测试与构建）。
- 视频运动指标对真实拍摄的准确性未验证；合成视频只证明方法可运行。
- Canvas 运镜播放、咖啡配方属 D5；反馈驱动修订未在 D4 Android 页面接入。
- 音频始终不分析；HEIC 在 API 26/27 设备上的转换能力未验证。
## 14. D4 复审修复（2026-11-05）

基线：`ba1eb52`（D4 功能/证据提交 `d532ce0`）。本轮只修以下两项，不进入 D5。

| 问题 | 修复 | 回归测试 |
|---|---|---|
| P1 反馈分析结束写回旧会话快照，覆盖分析期间保存的进度/计时或修订 | `feedback_service._persist_feedback` 在会话锁内重读最新会话，核对状态、计划版本与步骤；版本变化返回 409 `VERSION_CONFLICT` 且不写 Feedback；只合并 `evidence_levels[step_id]`，保留最新 `current_step_id`/`step_statuses`/`timer` | `test_feedback_analysis_keeps_progress_saved_while_model_runs`、`test_feedback_analysis_does_not_write_after_revision_changes_plan` |
| P2 视频观察缩略图复用视频开头预览 | 新增 `MediaLoader.extractEvidenceFrame`（`MediaMetadataRetriever` 按 timestamp 取帧）；`MediaViewModel` 按 `mediaId|frameIndex|timestampS` 生成证据帧；反馈页视频帧缺失显示“证据帧不可用”，不回退开头缩略图 | `videoEvidenceFramesFollowEachObservationTimestamp`、`missingEvidenceFrameIsUnavailableWithoutVideoThumbnailFallback` |

本轮实测：服务端 **90 passed / 0 failed**；安卓 **43 tests / 0 failures**（`MediaViewModelTest` 4 项）；`assembleDebug` BUILD SUCCESSFUL；APK 10,798,800 字节；`git diff --check` 通过；密钥扫描 262 文件、0 匹配、clean。真实拍摄图片/短片反馈仍为 **BLOCKED**（真机走查用的相册截图不是咖啡拍摄素材）。
## 15. D4 剩余 P2：证据帧以模型实际输入为准（2026-11-05）

基线：`40676b1`。只修“Android 本地按时间戳重新解码，不能保证与模型看到的帧一致”，不进入 D5。

| 问题 | 修复 | 回归测试 |
|---|---|---|
| Android 用 `OPTION_CLOSEST` 重新解码视频，显示的帧可能不是模型实际看到的帧 | 服务端在反馈写入时保存实际送入模型的视频帧到 `feedback_frames/{feedback_id}/frame_{index}.jpg`；新增 `GET /v1/feedback/{feedback_id}/evidence-frames/{media_id}/{frame_index}?timestamp_s=...`，校验 observation 的 `media_id/frame_index/timestamp_s` 后返回该 JPEG，不重新解码；Android 下载该字节并本地缓存，404/失败显示“证据帧不可用”，不回退开头缩略图 | 服务端 `test_video_evidence_frames_are_exact_model_input_frames`（同一短片 frame 0/1，端点字节与模型输入字节逐字节一致）；Android `videoEvidenceFramesUseServerProvidedBytesForEachObservation`、`missingEvidenceFrameIsUnavailableWithoutVideoThumbnailFallback` |

本轮实测：服务端 **91 passed / 0 failed**；安卓 **43 tests / 0 failures**；`assembleDebug` BUILD SUCCESSFUL；APK 10,816,510 字节；`git diff --check` 通过；密钥扫描 263 文件、0 匹配、clean。并发进度与计划版本冲突回归保留。上一轮 `videoEvidenceFramesFollowEachObservationTimestamp` 已由 `videoEvidenceFramesUseServerProvidedBytesForEachObservation` 取代（不再本地解码）。真实拍摄图片/短片反馈仍为 **BLOCKED**。
## 16. D5 摄影运镜与咖啡配方（2026-11-05）

基线：`fb05fde`。本轮只实现 D5，不进入 D6。

| 能力 | 实现 | 回归 |
|---|---|---|
| 摄影运镜 | Pydantic `CameraMoveSpec` 补齐 NaN/Infinity、组合、方向、时长/缓动、备注/局限校验；摄影提示词要求合法 `camera_move`；模型缺失“环绕”spec 时服务端生成带明确“非模型输出”说明的结构化 2D 兜底；Android `CameraMoveValidator` 同规则校验，`CameraPathCanvas` 区分机位移动/变焦/原地转向/静止，支持播放、暂停、重播、时间轴，非法数据只显示明确提示 | `test_camera`、`test_plan_photography`、`CameraMoveValidatorTest`、`CameraPlaybackStateTest`、`DtoTest` |
| 咖啡配方 | 新增 Recipe/RecipeVersion/Tasting/Adjustment/History/Compare 后端与 Android 页面；V60 演示 15 g / 225 g / 92 °C / 150 s；缺少磨豆机/电子秤/温控壶给替代提示；提示词明确口味不得由模型推断 | `test_recipe`、`RecipeViewModelTest` |
| 配方修订 | 服务端按实际参数判断单变量；多变量 422 `SINGLE_VARIABLE_REQUIRED`；`base_version` 冲突 409；校验失败不写新版本；旧版本只读；compare 仅参数与用户评分差异 | `test_recipe`、`RecipeViewModelTest` |

本轮实测：服务端 **108 passed / 0 failed**；安卓 **52 tests / 0 failures**（`CameraMoveValidatorTest` 3、`CameraPlaybackStateTest` 1、`RecipeViewModelTest` 3、`DtoTest` 5）；`:app:assembleDebug` BUILD SUCCESSFUL；APK **10,869,987 字节**。真实模型运行证据见 `codearts_proof/day5/real_flow.json`、`plan_photography_real.json`、`plan_coffee_real.json`。

真机（realme GT6 / RMX3800 / Android 16 / `eeffd16b`）：运镜播放/暂停/重播/时间轴通过；咖啡计划→配方 v1→品尝表单可见通过。口味保存、单变量调整与对比因工具权限拒绝未完成，标 **BLOCKED**（不重试、不伪造）；`real_flow.json` 中的口味值为脚本测试输入，不是真实用户品尝结论。
### 16.1 D5 补验：第三方实拍、时间轴拖动与咖啡 92→90（2026-11-05）

- **第三方公开授权实拍链路通过**：
  - CC0 照片 `Coffee cup seen from above.jpg`（1,003,643 字节，SHA-256 `351eb4...ac681`）；真实反馈 `unclear`，描述主体/构图/可见光线，无口味或安全推断。
  - CC BY-SA 4.0 短片 `A man pours Arabic coffee.ogv`（Sarah Canbel，原 1,037,297 字节；转 H.264 MP4 去音轨 486,725 字节，4.204204 秒）；主反馈 `unclear`，4/4 证据帧与模型输入逐字节一致；提交到“顺时针环绕拍摄 8 秒”步骤 3 的反例实际返回 `not_met`，明确指出去咖啡动作而非环绕，5/5 证据帧字节一致。
  - 素材来源、许可、SHA-256、页面副本与处理记录见 `codearts_proof/day5/third_party_assets.json`、`source/`、`third_party/README.md`、`third_party/real_feedback.json`；未用于微调/训练/冒充用户自拍。
- **用户自拍环绕反馈仍 BLOCKED**：没有用户自拍的“手机环绕咖啡 8 秒”素材；不能用倒咖啡短片冒充。第三方实拍通过不改变该 BLOCKED 状态。
- **运镜**：新增时间轴拖动 `CameraPlaybackState.seek()`，JVM 覆盖 seek 边界与暂停；真机本轮新 APK 已安装，但拖动时间轴未再次走查。
- **咖啡**：真实模型重跑 V60 92→90，v2 与 compare 的差值为 `water_temp_c 92→90, delta -2`；服务端按实际参数差异判断，0 变化返回 422 `no_parameter_change`，多变量仍 422 `SINGLE_VARIABLE_REQUIRED`。
- **真机咖啡**：v1 与用户评分已通过 UI 保存（服务端 201：酸4/甜3/苦2/醇厚3/香气4/余韵3/总体4，notes `sour mild finish short`）；按钮点击命中不稳定，92→90 调整与对比未在真机完成，断网重试未触发请求，均标 **BLOCKED**（权限拒绝，不重试/不伪造）。
- 本轮实测仍为服务端 **108 passed / 0 failed**、Android **52 tests / 0 failures**、`:app:assembleDebug` 成功、APK 10,869,987 字节。
### 16.2 D5 复审三项修复（2026-11-05）

1. **配方创建使用已确认计划参数**：`RecipeCreateRequest.demo` 默认 false，按计划文本解析 15/225/92/150；仅 `demo=true` 且计划与 V60 演示值一致时才用固定演示配方，否则 422 `demo_parameters_mismatch` 且不创建。新增非默认 18 g/270 g/90 °C/165 秒用例，断言计划、配方参数与步骤说明一致。
2. **可编辑变量与派生粉水比**：`ratio` 改为派生、不可直接编辑；只改水量 225→240 g 时 ratio 15→16 自动派生，不算第二个主动调整；新版本同步参数、用料与步骤文本，旧版本按原值回查。覆盖 225→240、92→90、多变量拒绝、版本冲突、直接改 ratio、非法值与失败不写入。
3. **Canvas easing**：新增 `CameraEasing`，位置/变焦/转向使用 eased progress，时间轴显示真实时间；`CameraEasingTest` 断言 linear 与 ease_in_out 在 0.25 时分别为 0.25/0.125，`CameraPlaybackStateTest` 覆盖拖动 seek。

本轮实测：服务端 **111 passed / 0 failed**；Android **55 tests / 0 failures**（`CameraEasingTest` 2、`RecipeViewModelTest` 4）；`:app:assembleDebug` BUILD SUCCESSFUL；APK **10,896,532 字节**；真实模型 V60 按计划解析并完成 92→90。

状态分列：第三方实拍链路通过；用户自拍环绕 BLOCKED；真机配方 92→90/对比 BLOCKED；真机断网重试 BLOCKED；真机 easing/拖动未复测。本轮提交 `189c1e6`，已推送并核验远端 `main`。
### 16.3 D5 配方复审再修（2026-11-06）

基线：`b47ba94`。只修三项：

1. **步骤更新按变量语义**：`_rewrite_steps()` 不再全局数字替换，改为按“咖啡粉/咖啡豆/粉量”“注水/水量/总注水”“水温/温度”“总时长/总时间/时长”“粉水比/比例”标签匹配；温杯/润洗用水不随粉量或 brew water 变化。回归覆盖咖啡粉 15→16 g 时温杯用水 115 g 不变、不同变量恰好同值不串改、新版参数/用料/步骤一致且 v1 原值可回查。
2. **中文冲煮时长**：支持 `总时长约 3 分钟`→180 秒、`2 分 30 秒`→150 秒、`150 秒`→150 秒。
3. **先校验后派生**：主动变量先做类型/范围校验，再计算粉水比；`dose_g=0` 与非数字输入返回 422 `INVALID_REQUEST`（`invalid_adjustment_value`），不写新版本。正常水量派生、单变量限制与版本冲突回归保留。

本轮实测：服务端 **114 passed / 0 failed**（配方测试 8 项）；Android **55 tests / 0 failures**；`:app:assembleDebug` BUILD SUCCESSFUL；APK **10,822,322 字节**；真实模型 V60 按计划解析重跑，92→90 一致。状态仍分列：第三方实拍通过；用户自拍环绕 BLOCKED；真机配方对比 BLOCKED；断网重试 BLOCKED；真机 easing/拖动未复测。
### 16.4 D5 配方复审收尾（2026-11-06）

基线：`1376a51`。只修两项：

1. **总水量与闷蒸/分段注水区分**：新增总量识别（`总注水/总水量/累计/最终/总计/继续注水至/注水至/加水至`）；“闷蒸注水 30 g，继续注水至 225 g”取 225 g，粉量 15 g→ratio 1:15；多个未标总量的注水量返回 422 `INVALID_REQUEST`（`water_total_ambiguous`），不创建配方、不猜测。
2. **显式总时长优先与中文分钟步骤改写**：`用时 30 秒。总时长 150 秒`→150 秒；`总时长 2 分 30 秒`→150 秒；调整 150→180 秒后新版参数与步骤说明均为 180 秒（步骤规范化为“总时长 180 秒”），旧版保留“2 分 30 秒”。

本轮实测：服务端 **116 passed / 0 failed**（配方测试 10 项）；Android **55 tests / 0 failures**；`:app:assembleDebug` BUILD SUCCESSFUL；APK **10,822,322 字节**；真实模型 V60 按计划解析总水量 225/ratio 1:15，92→90 链路通过。状态仍分列：第三方实拍通过；用户自拍环绕 BLOCKED；真机配方对比 BLOCKED；断网重试 BLOCKED；真机 easing/拖动未复测。
推送核验（2026-11-06）：`git ls-remote origin main` 开工为 `1376a51`，本地领先 3 个提交（`bd1fe0c`、`f32f4e6`、`0e254a2`）；`git push origin main` 正常快进成功（`1376a51..0e254a2`，未强推），远端 `main = 0e254a2`；推送后复跑服务端 **116 passed / 0 failed**、Android **55 tests / 0 failures**、`:app:assembleDebug --rerun-tasks` BUILD SUCCESSFUL、APK 10,822,322 字节、密钥扫描 298 文件 0 匹配、`git diff --check` 退出 0。未进入 D6。
### 16.5 D5 配方解析优先级修复（2026-11-06）

基线：`0e254a2`（本地 `864b211` 仅文档状态记录，不改代码）。只修两项，不进入 D6：

1. **总水量来源与优先级**：解析改为分层——先取显式总量（`总注水/总水量/注水总量/总水/总量/总计/合计/最终注水/最终水量`），存在显式总量时忽略任何阶段注水量；无显式总量时仅接受唯一累计终值（`继续注水至/注水至/注水到/加水至/加到/累计注水`）；多个不同累计值、多个阶段注水量或仅闷蒸/局部用水量 → 422 `INVALID_REQUEST`（`water_total_ambiguous`，`details.source` 为 `explicit_total`/`terminal_pour`/`stage_amount`/`local_only`），不创建配方。「闷蒸 30 g → 注水至 100 g → 注水至 150 g → 总水量 225 g」得到 **225 g**；「闷蒸注水 30 g，继续注水至 225 g」回归保留。
2. **总时长冒号与优先级**：显式 `总时长/总时间` 支持中英文冒号，先于任何单步用时；多个不同显式总时长 → 422 `brew_time_ambiguous`。调整总时长只改写显式总时长标签（`总时长/总时间/时长`），闷蒸等单步用时保持不变，旧版保留原值。

API 回归覆盖创建时实际保存的 `variables`、`ingredients` 与 `steps`，以及调整后的新版本与旧版本。本轮实测：服务端 **120 passed / 0 failed**（配方测试 14 项）；Android **55 tests / 0 failures**；`:app:assembleDebug --rerun-tasks` BUILD SUCCESSFUL；APK **10,822,322 字节**。状态分列不变：第三方实拍通过；用户自拍环绕 BLOCKED；真机配方对比 BLOCKED；断网重试 BLOCKED；真机 easing/拖动未复测。
### 16.6 D5 配方创建/调整总量一致性（2026-11-06）

基线：`991b4b6`。创建与调整改为共用同一套来源识别器：

1. **总水量**：共用 `_WATER_MENTION_PATTERN` 与显式/终值/阶段/局部分类；创建按显式总量 > 唯一累计终值 > 唯一普通水量取值，调整复用同一分类并按 span 精确改写被识别为总量的位置（显式总量或唯一终值），并同步改写同值的普通水量声明（`水/水量`）。阶段注水（`注水至 100 g`）、闷蒸局部量（`闷蒸 30 g`）与温杯/润洗用水不因数值相同而改写。`注水总量：225 g` 改 240 g 后参数、用料与步骤均为 240 g，旧版仍为 225 g。
2. **总时长**：创建优先显式 `总时长/总时间`（支持中英文冒号），调整复用同一显式匹配并按 expression span 只改该位置；`静置时长`/`闷蒸用时` 等单步时长不改。`总时长：150 秒，静置时长 150 秒` 改 180 秒后仅总时长为 180 秒，静置仍 150 秒。

API 回归新增 2 项并保留总水量优先、冒号总时长、多段注水/局部量 422 等旧用例。本轮实测：服务端 **122 passed / 0 failed**（配方测试 16 项）；Android **55 tests / 0 failures**；`:app:assembleDebug --rerun-tasks` BUILD SUCCESSFUL；APK **10,822,322 字节**。状态分列不变：第三方实拍通过；用户自拍环绕 BLOCKED；真机配方对比 BLOCKED；断网重试 BLOCKED；真机 easing/拖动未复测。
### 16.7 D5 配方调整总量来源定位（2026-11-06）

基线：`ac538ef`。创建与调整共用同一个「整份配方来源定位器」：

1. **总水量**：`_select_water_total` 同时服务创建与调整。调整时一次性扫描全部步骤字段，按显式总量 > 唯一累计终值 > 唯一普通水量声明的顺序确定来源，只更新该来源位置（及同值 `水/水量` 声明），不再逐字段猜测。`注水 225 g` 改 240 g 后 `water_g=240`、`ratio=16.0`、用料水 240 g、步骤 `注水 240 g`；旧版仍 225 g。
2. **总时长**：调整时一次性收集显式 `总时长/总时间`，只更新该 expression span；不同步骤的 `萃取用时 150 秒` 等单步用时保持不变。`总时长：150 秒` 改 180 秒后仅总时长更新，单步 150 秒；旧版仍 150 秒。
3. **旧配方保护**：步骤文本中找不到与当前参数值一致且唯一的来源时返回 422 `INVALID_REQUEST`（`total_source_unconfirmed`，`details.variable`），提示用户确认，失败不写入新版本。

API 回归新增 3 项并保留上轮全部用例。本轮实测：服务端 **125 passed / 0 failed**（配方测试 19 项）；Android **55 tests / 0 failures**；`:app:assembleDebug --rerun-tasks` BUILD SUCCESSFUL；APK **10,822,322 字节**。状态分列不变：第三方实拍通过；用户自拍环绕 BLOCKED；真机配方对比 BLOCKED；断网重试 BLOCKED；真机 easing/拖动未复测。
### 16.8 D5 配方创建期来源固化与停止条件同步（2026-11-06）

基线：`b7e923c`。把“调整时定位来源”前移为“创建时校验并固化可用来源”：

1. **创建期来源校验**：创建配方生成步骤后，用同一来源定位器校验 `water_g`、`brew_time_s` 能在 `instruction`/`target` 中定位；若只出现在标题/摘要，创建前返回 422 `INVALID_REQUEST`（`total_source_unconfirmed`，`details.variable`），提示在计划步骤中明确参数，不再创建“事后无法调整”的配方。
2. **停止条件同步**：调整总水量时，除显式总量与同值普通水声明外，**同值的终值/最终停止条件**（如 `继续注水至 225 g 后停止`）也一并更新；中途不同值的阶段注水（如 `注水至 100 g`）保持原值。`总水量 225 g / 中途 100 g / 最终至 225 g 停止` 改 240 g 后，新版总量、用料与停止条件均为 240 g，中途仍 100 g，旧版 225 g。
3. **旧数据兜底**：直接对无来源步骤调用定位器仍返回 422 `total_source_unconfirmed`，保留旧配方明确兜底。

API 回归新增 3 项（停止条件同步、摘要来源创建前确认、旧数据兜底）并保留全部既有用例。本轮实测：服务端 **127 passed / 0 failed**（配方测试 21 项）；Android **55 tests / 0 failures**；`:app:assembleDebug --rerun-tasks` BUILD SUCCESSFUL（35 tasks executed，重跑一次仍成功）；APK **10,822,322 字节**。状态分列不变：第三方实拍通过；用户自拍环绕 BLOCKED；真机配方对比 BLOCKED；断网重试 BLOCKED；真机 easing/拖动未复测。
### 16.9 D5 总水量下限校验（2026-11-06）

基线：`f840d03`。总水量调整后、写入新版本前增加中途累计注水目标校验：

- 收集步骤中未被本次更新的中途累计注水目标（`注水至/继续注水至/累计注水/注水` 等，按来源定位 span 排除已更新的总量/最终停止条件）。
- 若新总水量低于任一保留目标，返回 422 `INVALID_REQUEST`（`intermediate_water_exceeds_total`，`details.water_g`、`details.intermediate_targets`），不创建新版本；旧版本与历史保持原值。
- 回归：中途 `注水至 100 g`、最终 `继续注水至 225 g 后停止`，总量改 90 g 被拒绝（v1 与历史不变）；改 240 g 成功，中途仍 100 g、最终停止条件为 240 g。摘要来源创建期 422 回归保留。

本轮实测：服务端 **128 passed / 0 failed**（配方测试 22 项）；Android **55 tests / 0 failures**；`:app:assembleDebug --rerun-tasks` BUILD SUCCESSFUL（35 tasks executed）；APK **10,822,322 字节**。状态分列不变；未进入 D6。
### 16.10 D5 连续调整的中途/最终目标身份保留（2026-11-06）

基线：`43b6e23`。修复连续调整总水量时“仅凭数值相同就改写中途目标”的问题：

- `_locate_water_spans` 在显式总量来源下，只把**最终目标** terminal 纳入更新：标签为 `继续注水至/继续注水到/最终注水/最终水量`，或值后紧跟“后停止/即停止/后结束”；`注水至 X` 等中途累计目标即使与当前总量同值也不改写。
- 回归：初始 `总水量 225 g，中途注水至 100 g，最后继续注水至 225 g 后停止`；先改 100 g（v2 总量/最终 100、中途 100），再改 240 g（v3 总量/最终 240、中途仍 100）；v1/v2 历史按原值回查；改 90 g 仍 422 `intermediate_water_exceeds_total` 且不写入。
- 本轮实测：服务端 **129 passed / 0 failed**（配方测试 23 项）；Android **55 tests / 0 failures**；`:app:assembleDebug --rerun-tasks` BUILD SUCCESSFUL（35 tasks executed）；APK **10,822,322 字节**。状态分列不变：第三方实拍通过；用户自拍环绕 BLOCKED；真机配方对比 BLOCKED；断网重试 BLOCKED；真机 easing/拖动未复测。
### 16.11 D5 总量来源身份持久化（2026-11-06）

基线：`a90c82a`。把“总量声明/最终停止条件”的身份从自由文本猜测改为持久化来源标识：

- `Recipe` 新增可选 `total_sources`；创建时记录 `water_g` 的 marks（`step_index`/`field`/`label`/`kind`/`ordinal`/`role=declaration|final`），跨版本原样保留。
- `_is_final_water_target` 不再以 `继续注水至` 等标签作为判据，只认值后“后停止/后结束”或前文“最后/最终”；创建时只把被标记的位置记为 `final`。
- 调整时只按 marks 定位并更新总量声明与最终停止条件；中途 `继续注水至 100 g` 即使与总量同值也保持，“等待 10 秒”不变。无 `total_sources`（旧数据）或身份定位失败 → 422 `total_source_unconfirmed`，不写入。
- 回归：`总水量 225 g / 闷蒸后继续注水至 100 g，等待 10 秒 / 注水至 225 g 后停止`；改 90 g → 422；先改 100 g 再改 240 g → 最新版总量/最终 240 g、中途仍 100 g、等待仍 10 秒，v1/v2 历史按原值回查；无 marks 的旧配方 → 422。

本轮实测：服务端 **131 passed / 0 failed**（配方测试 25 项）；Android **55 tests / 0 failures**；`:app:assembleDebug --rerun-tasks` BUILD SUCCESSFUL（35 tasks executed）；APK **10,822,322 字节**。状态分列不变；未进入 D6。
### 16.12 D5 最后执行指令身份与旧配方恢复（2026-11-06）

基线：`ad81680`。两项修复：

1. **最后执行指令按结构判定**：不再靠追加停止词。若全部终值都与总量同值，则它们都是总量引用；若存在不同值的中途目标，则只把最后一个执行步骤中与总量同值的终值（且该步骤内这些终值全部为 `target` 或带“后停止/后结束/最后”标记）标为 final；无法确认时创建前 422。`总水量 225 g` + `分两次注水至 225 g，等滤杯滴完` 改 240 g 后，参数、用料与最后执行指令一致；旧版仍 225 g。
2. **旧配方恢复**：缺少 `total_sources` 时，首次调整若能在步骤文本中唯一确认来源，则自动补齐 marks 并写入新版本；同值歧义返回 422 `total_source_unconfirmed`（`confirmation_required=true`、`confirm_field=water_source_confirmation`、`candidates`），客户端用 `water_source_confirmation.declaration/final` 指定候选 ID 后重试；确认后写入新版本，旧版本与历史保持原值。

本轮实测：服务端 **134 passed / 0 failed**（配方测试 28 项）；Android **55 tests / 0 failures**；`:app:assembleDebug --rerun-tasks` BUILD SUCCESSFUL（35 tasks executed）；APK **10,822,322 字节**。状态分列不变；未进入 D6。
### 16.13 D5 总量与最终停止冲突检测 + Android 确认流程（2026-11-06）

基线：`3c86b6e`。两项修复：

1. **冲突检测**：显式总量与明确最终停止条件值不同（如 `总水量 225 g，最后注水至 220 g 后停止`）→ 422 `INVALID_REQUEST`（`water_total_conflicts_with_final`，`details.water_g`、`details.final_targets`）；创建、旧配方恢复、调整三条路径均拦截，不写入冲突版本。中途累计量低于总量的正常用例与 225→100→240 连续调整回归保留。
2. **Android 确认流程**：收到 `confirmation_required` 时展示候选步骤/字段/文本，用户分别勾选总量声明与最终指令；确认后沿用原调整参数与 `base_version` 重试；取消不发送请求；重试遇 409 时显示版本冲突并刷新。JVM 测试覆盖确认成功、取消、版本冲突。

本轮实测：服务端 **136 passed / 0 failed**（配方测试 30 项）；Android **58 tests / 0 failures**；`:app:assembleDebug --rerun-tasks` BUILD SUCCESSFUL（35 tasks executed）；APK **10,838,706 字节**。状态分列不变；未进入 D6。
### 16.14 D5 中途完成条件区分与确认完整性校验（2026-11-06）

基线：`3472e54`。三项修复：

1. **中途完成条件 vs 最终停止条件**：中途步骤 `target` 中的 `注水至 100 g` 不再参与总量冲突；只有最后一个执行步骤的最终目标（或带“最后/最终/后停止”标记）才是最终条件。回归：总水量 225、中途完成条件 100、最后 `注水至 225 g 后停止` 可创建；改 240 后中途仍 100、最终 240；真正的最终条件冲突仍 422。
2. **确认完整性**：服务端在写入前校验所选来源完整：存在最终指令时只选声明、遗漏最终 → 422 `invalid_water_source_confirmation`（`missing=["final"]`、`requires_final=true`），不写入新版本。Android 显示候选原文片段，并在缺少最终选择时提示“请选择最终执行指令”。
3. **类型化请求**：`water_source_confirmation` 使用严格类型模型（整数、非负、声明至少 1 项）；服务端校验候选 ID 范围、角色（final 必须 terminal 且值匹配总量）。非法类型/范围/角色 → 422 且不写入。

本轮实测：服务端 **137 passed / 0 failed**（配方测试 31 项）；Android **59 tests / 0 failures**；`:app:assembleDebug --rerun-tasks` BUILD SUCCESSFUL（35 tasks executed）；APK **10,838,706 字节**。状态分列不变；未进入 D6。
### 16.15 D5 confirmation_required 真机确认流程走查（2026-11-07）

基线：`bb6376c`。本轮只补文档与证据，未修改源码、测试与服务端代码，未进入 D6。设备 realme GT6 / RMX3800（`eeffd16b`）；APK 10,838,706 字节 / SHA-256 `363f886583541e8d814ce5d83f8eefd2d87b753a2cec67e8cce57480ac877728`（2026-11-07 11:51 重建）；服务端 `GET /v1/health` 200（`/health` 404），`adb reverse tcp:8000` 生效。

**场景构造**：复用旧配方会话 `sess_01M6P54DER9GF7SNX7ABT8GXBD` 的 v1 `recipe_01M6P5BDZT9557YX026QWNS4R6`（水 225 g / 粉 15 g / 92 °C / 150 秒）。该 v1 文件内**无 `total_sources`**，且 225 g 在步骤中以声明、累计注水、最终指令等多处同值出现，构成同值歧义旧配方。对 v1 直接提交 `water_g` 225→240 的调整返回 422 `total_source_unconfirmed`（`confirmation_required=true`、`requires_final=true`、候选 5 条），符合设计。

**API 补测（3 条 422，脚本 `work/probe_confirm_invalid.py`，结果 `work/probe_confirm_invalid2.json`）**：

- 缺 final（`declaration=[0]`、`final=[]`）→ **422** `invalid_water_source_confirmation`，`missing=["final"]`、`requires_final=true`。
- 非法 final（`final=[3]`，210 g 与总量 225 g 不等）→ **422**，`invalid=[3]`。
- 非法 declaration（`declaration=[3]`）→ **422**，`invalid=[3]`。
- 三例 `created` 均为 null，`versions_after` 仍仅 `v1[225]`；随后恢复 v2 成功（`versions_restored = v1[225] + v2[240]`）。
- 说明：早先脚本版本 `work/probe_confirm_invalid.json` 曾出现 201/409，原因是对角色假设过严（把 terminal 当 declaration 属契约允许，不构成缺陷，且当时多写的一个 v2 已清理），不作为产品缺陷记录。

**真机 8 项**：1 安装/启动 PASS；2 进入配方页 PASS；3 触发确认弹窗 PASS；3b 候选原文片段 PASS（5 行均含原文片段）；4 缺项提示 **BLOCKED（客户端 UI 缺陷）**；5 取消不写入 PASS；6 版本冲突 PASS（设备收到 409、提示已刷新并切到 v2）；7 确认成功 PASS（201 生成 v2 240 g / 1:16，界面“已创建 v2，只调整了 water_g。”，history `[(1,225,15),(2,240,16)]`，v1 原值未改）。结论 **7 PASS / 1 BLOCKED**。

**缺陷（分项 4）**：仅勾「总量」点「确认并重试」时，`RecipeViewModel.kt:348-350` 设置 `error="请选择最终执行指令。"` 后直接 return（未发请求），逻辑正确；但 `RecipeScreen.kt:98-105` 的 `ErrorBanner` 渲染在页面 Column，被叠加的 `WaterSourceConfirmationDialog`（`RecipeScreen.kt:331-379`，`AlertDialog` 起于 338）遮挡，弹窗打开期间该文案不可见，取消弹窗后才在页面顶部显示。需客户端在 Dialog 内展示校验错误后复测。

**最终数据状态**：v1 225 g（无 `total_sources`）+ v2 240 g（有 `total_sources`），adjustment `adj_01M6T2Y5M5NXQP4NH7HV360342`；冲突实验版本 `recipe_01M6T2HG72KP47MT1VBDV9QNE8` 已清理。

**本轮实测**：服务端 **137 passed / 0 failed**（20.70 s；`tests/test_recipe.py` 31 passed）；Android **59 tests / 0 failures / 0 errors**（14 个套件，`:app:testDebugUnitTest --rerun-tasks` BUILD SUCCESSFUL）；`:app:assembleDebug --rerun-tasks` BUILD SUCCESSFUL（35 tasks executed）；APK **10,838,706 字节**；密钥扫描 **309 文件 / 0 匹配 / clean=true / exit 0**。

**环境干扰**：步骤 7 期间外部应用 `com.hypergryph.arknights` 抢占前台致进程被杀，force-stop/start 后恢复 `last_session_id`；未清应用数据，非应用缺陷。

**Git**：`git push origin main` 连续 3 次 443 连接失败（exit 128），按规则停止重试，记为「已提交未推送」；未强推、未覆盖远端。状态仍在 D5，不进入 D6。
### 16.17 D5 confirmation 修复后真机复验（2026-11-07）

基线：`ebcccb1`。本轮修两项确认流程缺陷并复验，未进入 D6（本节编号按本轮任务约定为 16.17，16.16 无独立记录）。

| 问题 | 修复 | 回归 |
|---|---|---|
| 用户只确认一处总量声明时，其他同值 `explicit` 声明（总水量/总注水/注水总量/总水/总量/总计/合计/最终注水/最终水量）未更新 | 同值 `explicit` 声明一并更新；写入前对改写后的整份配方重新定位并校验总量唯一、最终停止条件一致 | `test_recipe.py`：step0 `instruction` 与 `target` 均 240 g；中途 100 g 保持；最终 240 g；v1 原值可回查 |
| 确认弹窗打开时错误文案被 `AlertDialog` 遮挡 | 错误提示渲染在同一 `AlertDialog` 内部；修改任一勾选清除旧错误；提交期间 `loading=true` 禁用勾选/确认/取消；取消/成功清错误 | `RecipeViewModelTest`：弹窗内错误、改选清错误、loading 禁用 |

- 写入前校验：遗漏最终条件造成冲突 → **422**，旧版保持原值、不创建/不调整。
- 改动文件（5 个）：`server/app/services/recipe_service.py`、`server/tests/test_recipe.py`、`android/.../recipe/RecipeScreen.kt`、`RecipeViewModel.kt`、`android/app/src/test/.../recipe/RecipeViewModelTest.kt`。

**本轮实测**：服务端 **138 passed / 0 failed**（18.60 s；`tests/test_recipe.py` **32 passed**，5.69 s）；Android **60 tests / 0 failures / 0 errors**（14 套件，`RecipeViewModelTest` 9，BUILD SUCCESSFUL in 28s）；`:app:assembleDebug --rerun-tasks` BUILD SUCCESSFUL（35 tasks）；APK **10,838,706 字节**，SHA-256 `f7894375db2f4fb95358c45b24e4f39614784681a28db255d6ece40cdc1e5bf9`，mtime 2026-11-07 12:57:54（晚于最后修改源码）；密钥扫描结果见 `codearts_proof/day5/secret_scan.json`。

**真机复验**（realme GT6 / RMX3800 / `eeffd16b`，8001 独立验收数据，`adb reverse tcp:8000 → tcp:8001`）：12 个分项 **全部 PASS**——启动/旧版参数、触发弹窗、弹窗内缺项提示（保留勾选、无写入）、改选后清提示、后端 422 拒绝时弹窗内错误且保留选择、取消不写入、409 版本冲突并刷新、恢复 v1、完整确认 201 生成 v2、v2 一致性与 v1 原值、真机「对比最近两个版本」渲染 v1→v2、收尾保留 v1+v2。C4 的 422 响应体未单独持久化，依据为 `app.log` 的 422、弹窗文案与目录无新增。

**四项验收状态（分列，不合并）**：真机确认流程（本轮）**PASS**；用户自拍环绕 **BLOCKED**（无用户自拍素材）；真机配方对比 **本轮 PASS**（真机入口渲染 water_g 225→240 Δ15、ratio 15→16 Δ1）；真机断网重试 **BLOCKED**（本轮未触发）。

`server/data/` 与 8000 正式数据服务未改动；8001 验收数据最终保留 v1 `recipe_01M6P5BDZT9557YX026QWNS4R6` + v2 `recipe_01M6T6F479SE3R4QBZB5V27SJG` 与 1 个 adjustment。详见 `codearts_proof/day5/review_fix_round17.md`、`device_verification.md`、`git_status.txt`。未进入 D6。
