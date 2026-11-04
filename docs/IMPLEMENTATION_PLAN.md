# 七天实施计划

> 计划日期：2026-11-04 起；比赛按 **11/17 前提交**准备（官网标题截止 11/18 与赛程 11/17 冲突，取更早日期；报名 11/5 由用户手工完成，不自动报名/提交）。
> 本计划只描述文档与后续编码阶段，**当前阶段不写应用代码、不安装软件、不推送/发布**。
> 所有“PASS”必须有真实命令输出/日志/截图；无法执行时写 `BLOCKED`，不得用静态数据或测试替身冒充。

## 1. 总体策略

1. **先打通真链路，再扩领域**：D1 环境/骨架/真实探针/最小垂直流程；D2 契约固化与完整文本流程；D3 步骤交互；D4 媒体；D5 运镜/咖啡；D6 四领域/参考资料/加固；D7 发布。
2. **风险前置**：构建/APK、DeepSeek 文本/视觉/JSON、视频抽帧、设备可用性在 D1–D4 暴露，不拖到 D7。
3. **契约先行**：先 Pydantic/kotlinx DTO/黄金样例，再写 UI/服务；字段改名必须双向测试。
4. **每日可演示垂直切片**：每天结束都有一个可安装/可调用的增量，不用“最后一天集成”。
5. **范围不削减**：四领域、参考教程、图片/短片反馈、运镜动画、咖啡配方历史、成果记录全部保留；时间不足只削减视觉打磨/附加动画类型（如额外曲线/多段运镜），不削减已确认能力。
6. **证据诚实**：无 Key/无设备/无视觉能力时标 `BLOCKED`；真实模型探针日志、构建日志、测试输出进 `codearts_proof/`。

## 2. 依赖顺序

```text
环境复测/本地 Git
  → 基础工程（Android + FastAPI + 健康检查）
  → DeepSeek 文本/图片/JSON 探针
  → 最小 DTO + 最小垂直流程（目标→澄清→真实计划→步骤卡，烹饪）
  → 契约固化 + 黄金样例 + 完整文本流程（烹饪）
  → 步骤 UX/进度/计时/暂停/恢复/提问（软件）
  → 媒体上传 + 图片/短片反馈（摄影）
  → 运镜 CameraMoveSpec + Canvas（摄影）
  → 咖啡配方/口味/单变量/历史
  → 参考教程导入（文本/文档/URL/图片/视频边界）
  → 四领域端到端 + 故障注入 + 密钥扫描 + Codex 审查
  → APK/README/视频/PPT/证据/提交包
```

依赖说明：

- D1 的模型探针与最小 DTO、D2 的契约固化必须先于 D3–D5；否则 DTO/错误码返工。
- D3 的步骤/进度/计时必须先于 D4 的反馈与 D5 的配方；否则没有上下文。
- D4 的媒体上传必须先于 D5 的摄影反馈演示；D5 的运镜 spec 可独立于视频反馈先做。
- D6 的参考资料导入必须在四领域演示前完成，否则演示只覆盖无资料路径。
- D7 只做发布/材料，不再加功能；发现阻断项回到对应日修复。

## 3. 逐日计划

### D1（11/04）：环境复测、基础工程、真实探针、最小垂直流程

**目标**：证明本机能构建/安装 Android、能启动 FastAPI、能真实调用 DeepSeek（或明确 blocked）；打通“输入目标→澄清问题→真实计划→步骤卡片”的最小垂直流程；建立文档/证据/Git 基线。

**交付物**

- `docs/ENVIRONMENT.md`：复测 JDK/Gradle/AGP/SDK/build-tools/设备/ffmpeg/Python/Key/GitHub，写命令与真实输出；不得复制本文快照冒充复测。
- `docs/IMPLEMENTATION_STATUS.md`：先建 CC_TASK 需求→任务/阶段→状态→证据映射，再写 D1 状态、阻塞、下一步。
- `codearts_proof/day1/`：prompt、命令、构建日志、探针日志、截图、测试输出。
- Android 骨架：单 module、Compose、`MainActivity`、健康/诊断页；最小目标输入、领域选择、澄清问题、简单计划页/步骤卡；无业务假数据。
- 服务端骨架：`GET /v1/health`、`GET /v1/capabilities`、配置加载、数据目录、统一错误信封。
- `scripts/probe_deepseek.py`：文本、图片、JSON mode、可选工具调用探针；输出脱敏 JSON/日志；无 Key 写 `blocked: NO_KEY`。
- 最小垂直流程：`POST /v1/sessions` 返回领域问题（问题可来自服务端规则库）→ `POST /v1/sessions/{id}/answers` → `POST /v1/sessions/{id}/plan-jobs` 真实模型生成 → `GET /v1/jobs/{id}` / `GET /v1/sessions/{id}/plan` → Android 显示简单计划/步骤卡；无 Key/失败时显示 `MODEL_NOT_CONFIGURED`/错误，不显示假计划。
- `.gitignore`、本地 `git init -b main`、首次提交（用户已同意版本管理时；若用户已提供 GitHub 私有仓库 URL，则推送；当前无凭据则只本地）。

**涉及文件**

```text
android/settings.gradle.kts
android/build.gradle.kts
android/gradle.properties
android/gradle/libs.versions.toml
android/gradle/wrapper/*
android/app/build.gradle.kts
android/app/src/main/AndroidManifest.xml
android/app/src/main/java/com/tutorialcoach/app/MainActivity.kt
android/app/src/main/java/com/tutorialcoach/app/TutorialCoachApp.kt
android/app/src/main/java/com/tutorialcoach/app/di/AppContainer.kt
android/app/src/main/java/com/tutorialcoach/app/data/ApiClient.kt
android/app/src/main/java/com/tutorialcoach/app/ui/screens/home/HomeScreen.kt
android/app/src/main/java/com/tutorialcoach/app/ui/screens/clarify/ClarifyScreen.kt
android/app/src/main/java/com/tutorialcoach/app/ui/screens/plan/PlanScreen.kt
android/app/src/main/java/com/tutorialcoach/app/ui/screens/step/StepScreen.kt
android/app/src/main/java/com/tutorialcoach/app/ui/screens/settings/DiagnosticsScreen.kt
android/app/src/main/java/com/tutorialcoach/app/data/{Dto.kt,SessionRepository.kt}
server/app/main.py
server/app/config.py
server/app/api/{health,sessions,plans,jobs}.py
server/app/models/{common,session,plan}.py
server/app/services/{store,model_client,plan_service,job_service}.py
server/app/prompts/plan_cooking.txt
server/requirements.in
server/requirements.txt
server/.env.example
scripts/probe_deepseek.py
```

**命令与预期**

```powershell
# 1) 会话级 JDK 21（不修改系统）
$env:JAVA_HOME = 'D:\Java\ideaIU-2025.2.win\jbr'
$env:Path = "$env:JAVA_HOME\bin;$env:Path"
java -version
# 预期：openjdk version "21.0.7"

# 2) 构建
cd C:\Users\wwx\Documents\Codex\2026-11-04\w\outputs\tutorial-coach\android
.\gradlew.bat --version
.\gradlew.bat :app:assembleDebug
# 预期：Gradle 8.9、JVM 21.0.7、BUILD SUCCESSFUL
# 产物：app/build/outputs/apk/debug/app-debug.apk

# 3) 设备/安装（当前无设备，必须先由用户连接真机或批准安装系统镜像）
adb devices
adb install -r .\app\build\outputs\apk\debug\app-debug.apk
adb shell am start -n com.tutorialcoach.app/.MainActivity

# 4) 服务端
cd ..\server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.in
pip freeze > requirements.txt   # 生成精确锁文件；提交
Copy-Item .env.example .env   # 用户手工填 Key；不要把 Key 贴到聊天/日志
uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
# 另开终端：
Invoke-RestMethod http://127.0.0.1:8000/v1/health

# 5) 反向转发
adb reverse tcp:8000 tcp:8000

# 6) 探针
python ..\scripts\probe_deepseek.py --output ..\codearts_proof\day1\model_probe.json

# 7) 设备手动最小垂直流程
# 打开 App → 输入“2 人份番茄鸡蛋面，30 分钟” → 回答至少 1 个问题
# （若服务端已 ready，记录原因并直接生成）→ 生成计划 → 看到步骤卡
# 失败时记录 UI 错误，不用示例计划冒充
```

**D1 闸门（必须逐项记录）**

| 闸门 | PASS 条件 | 失败时 |
|---|---|---|
| JDK/Gradle | `gradlew --version` = Gradle 8.9 + JVM 21.0.7 | 修正会话 `JAVA_HOME`/`org.gradle.java.home`；不得改用 JDK 25 |
| build-tools | 35.0.0 可用，或 36.0.0 经 AGP 实测成功 | 36 失败则请求用户批准安装 35；仍失败 `BLOCKED` |
| 构建 | `assembleDebug` 成功，APK 存在 | 保存完整日志；修工具链，不写假成功 |
| 安装/启动 | 真机或批准后的 AVD 安装成功、Activity 启动 | 当前无设备/AVD/镜像：`BLOCKED`，请用户连接真机或批准安装镜像；不得声称 PASS |
| 健康检查 | `/v1/health` 200，`status=ok/degraded`，无 Key 泄露 | 修服务端；记录真实错误 |
| 最小垂直流程 | 设备上：输入烹饪目标→回答问题→真实模型计划→看到步骤卡；无假数据 | 无 Key/设备/模型失败：记录 `BLOCKED`，UI 明确报错，不显示示例计划 |
| 模型文本 | 真实调用成功；或明确 `blocked: NO_KEY` | 无 Key 只能 blocked；不得用 mock 当成功 |
| 模型图片 | 真实调用成功/明确不支持；记录真实响应 | 未通过不得声称视觉可用；D4 前置阻断 |
| 模型 JSON | 返回可解析 JSON 且通过 Pydantic；失败有一次修复 | 记录 `MODEL_BAD_OUTPUT`；不进入 D2 假成功 |
| Git | 若已获准初始化/已有 Git，本地提交完成；有 remote 则 push 成功 | 无 Git/remote 记录 `BLOCKED`，不自行初始化、不伪造 GitHub 上传 |

**D1 结束动作**：按 `START_CODEARTS.md` 暂停并报告：修改文件、命令/真实输出、测试、截图路径、阻塞（设备/Key/build-tools/GitHub）、下一步。未获用户确认不进入 D2。

### D2（11/05）：契约固化、完整文本流程、烹饪

**目标**：把 D1 的最小垂直流程固化为完整契约与健壮文本流程；真实模型生成并校验烹饪计划；Android 完成“目标→两轮澄清→计划总览→步骤卡”闭环。

**交付物**

- 契约 DTO：Session/Question/Answer/Conditions/Plan/Step/Progress/Job/Error；`contracts/examples/` 至少 session/plan/error/job；D1 临时 DTO 全部对齐契约。
- 服务端：`POST /v1/sessions`、`POST /v1/sessions/{id}/answers`、`POST /v1/sessions/{id}/plan-jobs`、`GET /v1/sessions/{id}/plan`、`GET /v1/jobs/{id}`；完整 Pydantic 校验；JSON mode + 一次修复；失败错误码；条件/假设/安全字段。
- 领域提示词：烹饪；条件追问（最多两轮）；假设/完成标准/安全提示。
- Android：首页目标、领域选择、两轮澄清、计划总览、步骤卡（只读/前后切换）；Job 轮询/错误显示；无 Key 显示 `MODEL_NOT_CONFIGURED`。
- 测试：契约双向、条件/计划校验、Job 成功/失败、无 Key、非法 JSON、超时。
- `codearts_proof/day2/`。

**与 D1 的边界**：D1 已有最小目标→澄清→计划→步骤卡；D2 不重复造流程，只做契约对齐、校验/错误/提示词质量、两轮澄清和测试。D1 未完成真实模型闸门时，D2 的真实计划闸门仍 `BLOCKED`。

**文件/模块**

- `server/app/models/{session,plan,common}.py`、`services/{model_client,prompt_builder,plan_service,store,job_service}.py`、`api/{sessions,plans,jobs}.py`、`prompts/plan_cooking.txt`、`tests/`。
- `android/.../data/{Dto.kt,ApiClient.kt,SessionRepository.kt}`、`domain/{Model.kt,PlanValidator.kt}`、`ui/screens/{home,clarify,plan,step}`。
- `contracts/examples/`。

**命令/预期**

```powershell
cd server
pytest -q
# 预期：契约/校验/错误路径测试通过；mock 测试明确标记 mock；真实探针另跑

cd ..\android
.\gradlew.bat testDebugUnitTest
.\gradlew.bat :app:assembleDebug
# 安装后手动：烹饪目标→回答问题→生成计划→看到 3–15 步
```

**闸门**

- 真实模型生成计划，Pydantic 校验通过；日志含模型/耗时/状态，不含 Key/用户原文。
- 计划每步有可观察完成标准、时间、安全提示；`assumptions` 列出缺失条件。
- 无 Key/非法 JSON/超时 UI 明确，不显示假计划。
- 契约样例两端解析通过。
- 烹饪演示目标（2 人份番茄鸡蛋面）真实跑通。

**失败兜底**：无 Key → D2 只能完成契约/错误路径，真实模型闸门 `BLOCKED`；不要用静态计划进入 D3 演示。视觉未通过不影响 D2 文本，但 D4 会阻断。

### D3（11/06）：步骤 UX、进度/计时/暂停/恢复、提问、软件领域、修订锁定

**目标**：用户可真正按步骤练习；进度可保存/恢复；条件修改与计划锁定/修订规则落地；软件领域可跑。

**交付物**

- Android：步骤卡完整（上一步/下一步/暂停/恢复/计时/保存/进程死亡恢复）、提问面板、条件修改、反馈/修订入口占位、证据标签、离线横幅。
- 服务端：`PATCH /v1/sessions/{id}/progress`、`POST /v1/sessions/{id}/pause`、`POST /v1/sessions/{id}/resume`、`POST /v1/sessions/{id}/complete`、`POST /v1/sessions/{id}/abandon`、`POST /v1/sessions/{id}/ask`、`PATCH /v1/sessions/{id}/conditions`、`POST /v1/sessions/{id}/revision-jobs`、`POST /v1/sessions/{id}/revisions/{rid}/apply`、`POST /v1/sessions/{id}/revisions/{rid}/reject`；计划锁定 `PLAN_LOCKED`；条件 PATCH 3.2.1 语义。
- 软件领域提示词/问题/演示任务；Windows 命令只作为文本，不执行。
- 测试：计时重启锚点、暂停写入拒绝、进度合并、条件 null/空串、计划锁定、条件修订保留 done/skipped、409。
- `codearts_proof/day3/`。

**文件/模块**

- `android/.../domain/{TimerEngine.kt,PlanValidator.kt}`、`ui/screens/{step,ask,conditions,revision}`、`data/LocalStore.kt`。
- `server/app/services/{revision_service,progress_service}.py`、`api/{progress,ask,revisions}.py`、`prompts/{ask,revision,plan_software}.txt`。
- `server/tests/test_progress.py`、`test_conditions.py`、`test_revisions.py`、`test_timer`（Android JVM）。

**命令/预期**

```powershell
cd server
pytest -q tests/test_progress.py tests/test_conditions.py tests/test_revisions.py
cd ..\android
.\gradlew.bat testDebugUnitTest
.\gradlew.bat :app:assembleDebug
```

**闸门**

- 上一步/下一步/暂停/恢复/计时/保存可用；旋转/退后台/杀进程恢复；设备重启弹窗确认，不出现负计时。
- 用户点完成只 `self_reported`；模型不自动改状态。
- 有进度时 `POST /v1/sessions/{id}/plan-jobs` 返回 409 `PLAN_LOCKED`；条件修订 `feedback_id=null + request_reason` 只改未完成步骤；done/skipped 不变；Job 写盘前二次检查 `base_plan_version` 与进度/计时器，提交窗口内出现进度则失败且不覆盖。
- 条件 PATCH：省略/非空/null/空字符串行为与契约 3.2.1 一致；关键字段 null 原子失败。
- 提问 60s 端点/45s 模型/75s 客户端超时一致；失败可重试。
- 软件演示任务真实计划；不自动执行命令。

### D4（11/07）：媒体上传、图片/短片反馈、摄影领域

**目标**：用户上传照片/短片，获得带证据/时间戳/局限的反馈；摄影领域可跑；视频运动指标有真实方法。

**交付物**

- 服务端：`POST /v1/media`、`POST /v1/sessions/{id}/feedback-jobs`、`GET /v1/feedback/{id}`、`GET /v1/sessions/{id}/feedback`、ffprobe/Pillow/抽帧、`vidstabdetect` 运动统计、媒体限制、错误码；反馈 Pydantic 校验（观察必须有证据）。
- Android：Photo Picker、图片压缩/HEIC 转 JPEG、视频选择/大小校验、上传进度、反馈结果页、证据缩略图/时间戳、隐私提示。
- 摄影领域提示词/问题/演示任务；摄影计划按契约返回 `CameraMoveSpec`（D5 完成 Canvas 播放；本阶段可 `visual_aid=null` 并明确提示，不伪造动画）。
- 测试：图片格式/大小、视频时长/大小/解码失败、1–4 图/1 视频、证据缺失拒绝、运动失败 `motion_metrics=null`、音频 `false`。
- `codearts_proof/day4/`：真实图片/短片反馈日志、抽帧时间戳、限制说明。

**文件/模块**

- `server/app/services/{media_service,ffmpeg,feedback_service}.py`、`api/{media,feedback}.py`、`prompts/feedback.txt`、`prompts/plan_photography.txt`。
- `android/.../data/MediaRepository.kt`、`ui/screens/{media,feedback}`、`platform/MediaPicker.kt`。
- `server/tests/test_media.py`、`test_feedback.py`、`test_motion.py`。

**命令/预期**

```powershell
cd server
pytest -q tests/test_media.py tests/test_feedback.py tests/test_motion.py
# 生成合成视频（测试用；不是演示真实拍摄）
ffmpeg -f lavfi -i testsrc=size=640x360:rate=30:duration=8 -c:v libx264 -pix_fmt yuv420p ..\codearts_proof\day4\synthetic.mp4
# 上传→反馈，检查时间戳/证据/限制
cd ..\android
.\gradlew.bat testDebugUnitTest
.\gradlew.bat :app:assembleDebug
```

**闸门**

- 真实图片反馈：每条观察有图片证据；证据不足 `unclear/not_verified`；不判断内部温度/口味。
- 真实短片反馈：带时间戳；定性最多 8 帧；运动指标有方法/局限；不分析音频；不编造精确评分。
- 视频 ≤30s/≤100 MiB 被执行；超限明确错误。
- 上传失败可重试；不创建假 Feedback。
- 摄影演示任务真实计划+反馈。
- 真实素材由用户 11/6 前提供；未提供则真实反馈闸门 `BLOCKED`，合成视频只用于技术测试，不得当演示素材。

**失败兜底**：视觉探针未通过 → D4 反馈闸门 `BLOCKED`；可保留媒体上传/技术指标与明确“模型视觉不可用”，不得用假观察。视频运动失败 → `motion_metrics=null` + limitation，仍可给基于帧的定性观察。

### D5（11/08）：运镜 CameraMoveSpec/Canvas、咖啡配方

**目标**：摄影运镜路径/动画可播放且参数可校验；咖啡配方版本/口味/单变量/历史/对比可用。

**交付物**

- `CameraMoveSpec` DTO/校验器（机位/朝向/变焦/静止；坐标/时长/缓动/限制）；Android Canvas 路径+播放动画；非法参数拒绝。
- 咖啡 Recipe/Tasting/Adjustment/History/Compare API + UI；单变量强校验；照片不推断口味。
- 测试：CameraMoveSpec 一致性/边界/NaN；配方版本链/单变量/409/对比；UI 动画播放。
- `codearts_proof/day5/`。

**文件/模块**

- `android/.../domain/{CameraMoveValidator.kt}`、`ui/components/CameraPathCanvas.kt`、`ui/screens/recipe`。
- `server/app/models/{camera,recipe}.py`、`services/recipe_service.py`、`api/recipes.py`、`prompts/plan_coffee.txt`。
- `server/tests/test_camera.py`、`test_recipe.py`。

**命令/预期**

```powershell
cd server
pytest -q tests/test_camera.py tests/test_recipe.py
cd ..\android
.\gradlew.bat testDebugUnitTest
.\gradlew.bat :app:assembleDebug
```

**闸门**

- 摄影计划含合法 `CameraMoveSpec`；Canvas 区分机位/朝向/变焦；动画可播放/暂停/重播；不执行模型代码。
- 非法 spec（缺少路径、越界、NaN、shot_type/motion_type 不一致）被拒。
- 咖啡配方 v1→tasting→单变量调整→v2→history/compare；单变量强校验；口味只来自用户。
- 照片不推断口味；对比只给参数/用户评分差异。

### D6（11/09）：参考教程、四领域端到端、加固、彩排

**目标**：四领域各一条真实演示；参考资料边界可用；失败路径/密钥/日志/离线加固；Codex 审查。

**交付物**

- 参考教程：文字同步、文档/URL/图片/视频 Job；PDF 文本层/扫描件拒绝、DOCX、URL SSRF、字符上限/总预算不截断、注入包裹。
- 四领域演示任务全部跑通（烹饪/摄影/软件/咖啡）；记录/成果/历史。
- 故障注入：无 Key、401/402/429、超时、非法 JSON、媒体失败、服务重启、版本冲突、计划锁定、条件 null。
- 日志脱敏、秘密扫描、`.gitignore` 检查、README 草稿。
- Codex 审查；`codearts_proof/day6/`。
- `docs/IMPLEMENTATION_STATUS.md` 更新。

**文件/模块**

- `server/app/services/reference_service.py`、`security.py`、`api/references.py`、`prompts/reference_*`。
- `android/.../ui/screens/references`、`records`、`settings`。
- `server/tests/test_references.py`、`test_injection.py`、`test_failures.py`。
- `scripts/verify-submission.ps1` 初版。

**命令/预期**

```powershell
cd server
pytest -q
# 预期：全部通过；真实 Key 测试不在默认套件
cd ..\android
.\gradlew.bat testDebugUnitTest
.\gradlew.bat :app:assembleDebug
# 故障注入手工/脚本：无 Key、429、超时、坏媒体、服务重启
```

**闸门**

- 四领域演示各一条真实端到端；不是静态数据。
- 参考：文字/文档/URL 文本可用；扫描 PDF/登录页/视频平台链接明确拒绝；注入样例不改变系统行为；超 20k 拒绝不截断。
- 所有失败有 UI/重试；无假结果；密钥扫描通过。
- Codex 阻断项为 0 或明确记录未解决（不得带病进入 D7 演示）。

### D7（11/10）：发布与比赛材料

**目标**：可安装 APK、README/脚本、3 分钟视频、PPT、码道证据、提交包；不自动报名/提交。

**交付物**

- `submission/`：ppt、readme、源码包说明、视频（≤3 分钟）、codearts_proof、开源组件/许可证、部署运行、码道总结。
- `README.md`：依赖、服务端启动、Key 配置、APK 安装、`adb reverse`、四领域演示、限制/隐私、排错；明确 APK 非独立联网。
- 一键脚本：`setup-server.ps1`、`run-server.ps1`、`build-apk.ps1`、`install-apk.ps1`、`verify-submission.ps1`；不嵌 Key。
- 最终 APK（debug；release 签名不在本期）、干净安装/启动截图。
- Git 标签 `v1.0.0-submission`（若 remote 已配置则推送）；记录 commit hash。
- 视频脚本/录制清单、PPT 10 页、CodeArts 证据索引。

**命令/预期**

```powershell
# 干净构建/安装
cd android
.\gradlew.bat clean :app:assembleDebug
adb install -r .\app\build\outputs\apk\debug\app-debug.apk
adb shell am start -n com.tutorialcoach.app/.MainActivity

# 提交前检查
cd ..
powershell -ExecutionPolicy Bypass -File .\scripts\verify-submission.ps1
# 预期：无 .env/Key/keystore/构建垃圾；APK 存在；材料齐全；视频≤3分钟
```

**闸门**

- 干净安装/启动；四领域演示可用；无 Key；D7 产出草稿视频 ≤3 分钟（最终版 11/12 重录、11/16 定稿）；README 准确；codearts_proof 完整脱敏。
- 11/16 提交包就绪；11/17 前提交（用户手工）；不自动报名/提交/发布商店。

## 4. 缓冲与截止

| 日期 | 安排 |
|---|---|
| 11/04–11/10 | D1–D7 |
| 11/11–11/13 | 修复 D1–D7 阻断项、补测试、录制备用素材 |
| 11/14 | 功能冻结；只修阻断/文案/演示脚本 |
| 11/15–11/16 | 提交包定稿、视频/PPT/README/证据复核；11/16 包就绪 |
| 11/17 | 用户提交（不自动） |
| 11/18 | 官网标题截止（与赛程 11/17 冲突；以 11/17 为准，人工复核官网） |

- 报名 11/5：用户手工完成；队伍 1–5 人；不擅自报名/提交。
- 官网页面为 JS 渲染，当前只读到标题；日期冲突必须由用户登录官网复核并截图存档。
- 若 D1 设备/Key 阻塞超过 1 天：先做契约/错误路径/UI 骨架，但真实模型/媒体闸门保持 `BLOCKED`；不得用假数据推进演示。

## 5. 每日完成定义（DoD）

1. 当天代码/文档变更已提交（本地；有 remote 则推送）。
2. 当天命令真实运行，日志/输出存 `codearts_proof/dayN/`。
3. 新增契约字段有黄金样例/双向测试。
4. 错误路径有测试或手工验证；未验证项写 `docs/IMPLEMENTATION_STATUS.md`。
5. 无 Key/秘密/个人媒体进入 Git/日志/截图。
6. Codex 审查（至少阻断项清单）。
7. 当天演示路径可重复；不能重复的标 `BLOCKED`。

## 6. 测试与审查节点

| 节点 | 测试 | 审查 |
|---|---|---|
| D1 | 构建、健康、探针（真实/blocked）、最小垂直流程 | 环境/证据/密钥；START_CODEARTS 暂停报告 |
| D2 | 契约双向、计划校验、Job/错误 | 契约一致、真实模型日志、无假计划 |
| D3 | 计时/恢复/暂停/条件/修订/锁定/提问超时 | 证据等级、计划锁定、done/skipped 不变 |
| D4 | 媒体限制/抽帧/证据/运动失败/音频 false | 证据诚实、视频局限、无精确评分 |
| D5 | CameraMoveSpec/配方单变量/历史对比 | 结构化动画、无代码执行、口味只来自用户 |
| D6 | 参考边界/注入/故障注入/四领域 | 全量需求追踪、秘密扫描、Codex 阻断项 |
| D7 | 干净安装/材料检查 | 提交包、视频≤3min、README 准确 |

## 7. 需求追踪矩阵

| CC_TASK 要求 | 文档 | 阶段 | 验收 |
|---|---|---|---|
| Android APK/非 WebView | PRODUCT 2.1、TECH 1/6 | D1 | AC-01 |
| 四领域 | PRODUCT 5 | D2/D3/D4/D5/D6 | AC-06 |
| 目标入口 | PRODUCT P-01 | D1/D2 | AC-06 |
| 参考教程/边界 | PRODUCT 6、API 4.7 | D6 | AC-15/16 |
| 条件追问 | PRODUCT P-03 | D1/D2 | AC-06 |
| 准备/步骤/时间/标准 | PRODUCT P-04/05 | D1/D2 | AC-06 |
| 步骤卡/提问/暂停/计时/保存 | PRODUCT P-05/06、API 4.3 | D3 | AC-07/08 |
| 修改条件 | PRODUCT P-05、API 4.3 | D3 | AC-08/08b |
| 照片/短片反馈 | PRODUCT P-07、API 4.4 | D4 | AC-09/10 |
| 运镜 spec/动画 | PRODUCT P-05、API 3.6 | D5 | AC-11 |
| 咖啡配方/历史 | PRODUCT P-10、API 4.6 | D5 | AC-12 |
| 成果/记录 | PRODUCT P-09、API 3.13 | D3/D6 | AC-18 |
| 真实 DeepSeek/Key 服务端 | TECH 3.3、API 1.3 | D1 | AC-03/04/05/14 |
| 视频抽帧/不分析音频 | API 3.8/7 | D4 | AC-10 |
| 食物安全/口味边界 | PRODUCT 5.2 | D4/D5 | AC-09/12 |
| 失败恢复 | PRODUCT 8、API 8 | D6 | AC-13 |
| 比赛材料/日期 | COMPETITION_CHECKLIST | D7 | AC-20 |

## 8. 风险优先验证

1. **D1 工具链**：JDK 25 不能跑 Gradle；JBR 21；build-tools 35 缺失；无设备/AVD/镜像 → APK 闸门可能 `BLOCKED`。
2. **D1 模型**：无 Key；文本/图片/JSON/工具调用未验证；视觉失败会阻断 D4。
3. **D4 视频**：ffmpeg 抽帧/vidstabdetect 格式/性能；稀疏帧不能编造评分。
4. **D3 计划锁定**：有进度后禁止全量重生成；条件修订只改未完成步骤；提交时二次检查。
5. **D6 参考资料**：SSRF/注入/超长；拒绝而不截断。
6. **D7 部署说明**：APK 非独立联网；README/视频必须讲清楚，避免评委误判。

## 9. 不允许的“伪完成”

- 用静态 JSON 计划/反馈代替真实模型结果。
- 用 mock 测试通过冒充真实探针成功；测试名/日志未标 `mock`。
- 没运行 `assembleDebug` 就写 APK 成功；没安装就写启动成功。
- 没设备/AVD 就写“模拟器可用”。
- 没 Key/视觉失败就写“图片/视频分析已完成”。
- 用稀疏帧写 0–100 稳定性评分。
- 从照片判断内部温度/食用安全或咖啡口味。
- 用户点下一步就写“模型已验证完成”。
- 超长参考资料静默截断后当完整。
- 有进度时全量重生成覆盖已完成步骤。
- 提交包含 Key/`.env`/个人媒体/构建垃圾。
- 伪造 GitHub 推送/码道使用痕迹。

## 10. GitHub 与版本节点

- 当前：项目无 `.git`，无 `gh`/SSH/GitHub 凭据/remote；不能直接推送。
- 用户创建私有空仓库并提供 HTTPS URL 后：本地 `git init -b main` → 提交 → `git remote add origin` → 用户完成 GCM 登录/推送；或用户批准安装 `gh` 并 `gh auth login`。
- 每日提交；标签：`v0.2.0-d1` … `v0.8.0-d7`；最终 `v1.0.0-submission`。
- 不提交 `.env`、`local.properties`、`server/data/`、`.venv/`、`android/build/`、APK、keystore、个人媒体。
- 若 D1 已有 Git 但无 remote：本地提交继续，在 `IMPLEMENTATION_STATUS.md` 记 `GitHub: BLOCKED (no remote/credentials)`，不得写已上传。
- 若 D1 仍未初始化 Git 且用户未明确同意：不自行 `git init`，记 `Git: BLOCKED (no repo/approval)`；这不影响应用代码阶段，但版本管理证据缺失需在报告中说明。

## 11. 人工待办（与 RISK_REGISTER 同步）

| 待办 | 责任 | 时点 | 失败处理 |
|---|---|---|---|
| 填 `server/.env` 的 DeepSeek Key | 用户 | D1 前 | 无 Key：探针 blocked；不得假成功 |
| 连接真机并开 USB 调试，或批准安装系统镜像 | 用户 | D1 | APK 闸门 BLOCKED；不写 PASS |
| 批准安装 build-tools 35（若 36 不兼容） | 用户 | D1 | 构建 BLOCKED；记录错误 |
| 创建 GitHub 私有空仓库并提供 URL/登录 | 用户 | D1 后 | 本地 Git 继续；不伪造推送 |
| 确认最终产品名/图标 | 用户 | D1 前 | 用暂定名；不改架构 |
| 确认部署形态（本地演示 vs 后续服务端） | 用户 | D6 前 | 文档标“待确认”，不擅自公网部署 |
| 准备演示素材（自制菜品/咖啡/短片；无敏感信息） | 用户 | 11/6 前阶段素材；11/12 前最终录制 | 用合成素材仅测试，不冒充真实拍摄 |
| 官网复核 11/17 vs 11/18、报名 11/5、提交要求 | 用户 | 11/4–11/5 | 不擅自报名/提交；按 11/17 准备 |
| 最终提交 | 用户 | 11/17 前 | 不自动提交 |

## 12. 变更记录

| 日期 | 变更 |
|---|---|
| 2026-11-04 | 初版；按 Codex 审查修正条件 PATCH、参考资料不截断、计划锁定/条件修订、部署待确认、超时分层、计时重启；补 D1–D7 闸门 |
| 2026-11-04 | 对齐 START_CODEARTS：D1/P0 补齐“目标→澄清→真实计划→步骤卡”最小垂直流程；D2 改为契约固化/完整文本，避免重复实现 |
