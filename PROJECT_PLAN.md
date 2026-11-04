# 实践陪练（tutorial-coach）项目主计划

> 码道 Agent Space 交接主入口。开始任何实现前，先完整阅读本文件与 `docs/` 规格。
> 当前状态（2026-11-04）：规格/契约/计划/提示词文档已整理，**尚未写应用代码、尚未安装/推送/报名/提交**。
> 主要代码必须由码道生成并保存生成、调试、重构、Prompt 证据；Codex 负责审查；Claude Code 本阶段只做规划。

> 配置更新（2026-11-04）：用户已指定远程仓库 `https://github.com/wuwangxuan1-blip/tutorial.git`，本地仓库已接续其原有 main 历史。服务端密钥已写入本地 `server/.env` 并被 Git 忽略；不读取或输出密钥值。旧文档中的“无仓库/未提供Key”属于规划时快照，开工时以当前配置与实际探针为准；密钥保存不代表模型调用已验证。

## 1. 一句话目标

做一个**原生 Android 可安装 App**：用户输入一个实践目标（可附参考教程），App 按领域澄清条件，生成准备清单、分步骤计划、预计时间和可观察完成标准；用户逐步练习、随时提问、计时/暂停/修改条件，上传照片/短片获得有证据的反馈，并在烹饪、摄影/视频、软件/数字技能、咖啡/饮品四个领域留下可回查的成果与配方记录。

**不是**网页/PWA/WebView 套壳，也不是只会聊天的教程摘要工具。

## 2. 不可削减的需求

- 四领域全部保留：烹饪与烘焙；摄影与视频（含运镜）；软件操作与数字技能；咖啡与饮品。
- 目标为主入口，可附加文字/文档/链接/用户媒体参考教程；明确导入边界。
- 按材料、器具、版本、基础、时间、人数/份量、偏好等追问；生成准备、步骤、时间、可观察标准。
- 步骤卡 + 随时提问 + 上一步/下一步 + 暂停 + 修改条件 + 计时 + 保存/恢复。
- 用户主动上传照片/截图/短片；结合步骤与条件分析、追问、补救、调整后续步骤；**不做实时摄像头**。
- 摄影：构图/布光/推近/拉远/横移/摇镜/简单环绕；区分机位移动与镜头朝向；结构化可校验路径 + 可播放动画；**不执行模型生成代码**。
- 咖啡：器具/原料适配、比例、步骤、计时、用户口味、一次改一个变量、配方历史/对比；**不从照片推断口味**。
- 成果/照片/参数/配方/问题/调整历史可回查；**用户点下一步不等于模型验证完成**。
- 图片不能判断食品内部温度/食用安全；短片不能凭稀疏帧编造精确评分；无语音能力不伪造转写。
- 失败（断网/超时/限流/非法 JSON/媒体失败）有明确恢复；**不静默返回假结果**。
- Key 仅在服务端；APK、Git、日志、演示、截图不得含 Key。

## 3. 技术栈与版本基线

| 层 | 选择 | 版本/说明 |
|---|---|---|
| Android | Kotlin + Jetpack Compose + Material3 | Kotlin 2.0.21；Compose BOM 2024.12.01；单 module |
| 构建 | Gradle + AGP | Gradle 8.9（已缓存）+ AGP 8.7.3（已缓存）；**不用未缓存的 AGP 8.8.2** |
| JDK | JBR 21.0.7 | 会话级 `JAVA_HOME` + `org.gradle.java.home`；**默认 JDK 25 不能跑 Gradle 8.9**；不改系统变量 |
| SDK | compileSdk/targetSdk 35，minSdk 26 | platforms 34/35 已装；**build-tools 35.0.0 缺失**，先试 36.0.0，失败需用户批准安装 35 |
| 网络/序列化 | OkHttp 4.12.0、kotlinx.serialization 1.7.3 | 超时分层见 API 1.3 |
| 服务端 | Python 3.12 + FastAPI + uvicorn + Pydantic v2 | 本地 `127.0.0.1:8000`；单进程；JSON 文件原子写；无数据库 |
| 模型 | DeepSeek 官方 API | `base_url=https://api.deepseek.com`；模型名环境变量；主流程 JSON mode + Pydantic + 一次修复；不依赖工具调用 |
| 媒体 | ffmpeg/ffprobe 7.0.2 + Pillow + numpy | 视频抽帧/运动估计；不打包 ffmpeg；不分析音频 |
| 联调 | `adb reverse tcp:8000 tcp:8000` | 开发/比赛路径；APK 非独立联网；部署形态待用户确认 |

**当前环境阻塞（必须首日复测，不得假设已通过）**

- 无 DeepSeek Key：探针只能明确 `NO_KEY`/BLOCKED；不得 mock 冒充。
- 无 AVD、无系统镜像、`adb devices` 为空：D1 安装/启动可能 BLOCKED；需用户连接真机或批准安装镜像。
- build-tools 35 缺失、sdkmanager 12.0 有 XML v4 警告：先试 36，失败请求批准。
- GitHub：无 `gh`/SSH/凭据/remote；项目尚未初始化 Git；不能直接推送。
- 无 Android Studio：用 Gradle CLI + 真机/截图；Compose 预览不是硬依赖。

## 4. 架构与数据流

```text
Android (Kotlin/Compose)
  → HTTP/JSON + multipart → FastAPI (127.0.0.1:8000)
      → DeepSeek API（文本/图片；Key 仅服务端）
      → ffmpeg/ffprobe（校验/抽帧/运动指标）
      → 本地 JSON 文件（原子写；sessions/jobs/media/references）
```

- 单 Android module；手写 `AppContainer`；不引入 Hilt/Room/KSP。
- 长任务统一 Job + 轮询；不实现 SSE。
- 进度/计时本地持久化 + 服务端同步；服务端为恢复权威副本。
- API `/v1`、snake_case、ISO-8601 UTC、前缀 ID、统一错误信封、幂等键、乐观并发。
- 计划锁定：有任何进度/当前步骤/计时器时 `POST /v1/sessions/{id}/plan-jobs` → 409 `PLAN_LOCKED`；只能条件修订（`feedback_id=null` + `request_reason`）或新建会话；Job 写盘前二次检查版本与进度。
- 参考资料单条/合计 ≤20,000 字符；超限拒绝、不截断。
- 超时分层：ask 模型 45s/端点 60s/客户端 75s；Job 模型 90s/总 180s；媒体上传 180s；轮询 GET 15s。
- 计时恢复：`anchor_elapsed_ms` + `saved_at_epoch_ms`；设备重启检测；暂停写保护；不出现负值。

## 5. 文档索引（必须按序读）

| 文档 | 作用 |
|---|---|
| [docs/PRODUCT_REQUIREMENTS.md](docs/PRODUCT_REQUIREMENTS.md) | 用户故事、页面、四领域、状态机、AC-01–AC-20 |
| [docs/TECH_STACK.md](docs/TECH_STACK.md) | 选型比较、版本、环境、构建/部署、数据流 |
| [docs/API_CONTRACT.md](docs/API_CONTRACT.md) | **唯一契约源**：模型/端点/示例/错误/超时/状态机 |
| [docs/CODING_STANDARDS.md](docs/CODING_STANDARDS.md) | Kotlin/服务端/模型输出/安全/测试/Git/审查 |
| [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) | D1–D7 依赖、文件、命令、闸门、追踪矩阵 |
| [docs/CODEARTS_PROMPTS.md](docs/CODEARTS_PROMPTS.md) | P0–P6 可复制 Prompt + 报告/审查/回滚模板 |
| [docs/COMPETITION_CHECKLIST.md](docs/COMPETITION_CHECKLIST.md) | PPT/视频/README/证据/许可证/提交检查 |
| [docs/RISK_REGISTER.md](docs/RISK_REGISTER.md) | 风险、人工待办、验证命令、关闭标准 |
| [docs/README.md](docs/README.md) | 文档导航、术语、审查修复索引 |
| [START_CODEARTS.md](START_CODEARTS.md) | 首阶段暂停/证据/环境约束 |

## 6. 首阶段入口（P0）

**只执行 `docs/CODEARTS_PROMPTS.md` 的 P0**，不要一口气做完整 App。P0 边界：

1. 环境复测（JDK/Gradle/AGP/SDK/build-tools/设备/ffmpeg/Python/Key/GitHub），写 `docs/ENVIRONMENT.md`。
2. 版本管理：经用户同意或已有 Git 时初始化/提交并加 `.gitignore`；无 remote/凭据不推送，记 `BLOCKED`；未获同意记 `BLOCKED: NO_GIT_REPO`，不自行初始化。
3. Android 骨架 + 健康/诊断页；服务端 `/v1/health`、`/v1/capabilities`。
4. 探针：文本/图片/JSON/可选工具调用，真实日志；无 Key 标 `NO_KEY`。
5. **最小垂直流程**：输入烹饪目标 → 澄清问题 → 真实模型计划 → 简单步骤卡；无 Key/失败显示错误，不显示假计划。
6. `codearts_proof/day1/` 证据；`docs/IMPLEMENTATION_STATUS.md` 状态。
7. 构建 APK；有设备安装/启动/截图，无设备标 BLOCKED。
8. 按报告模板汇报，**暂停等待确认**，不自动进入 P1。

## 7. 七天闸门

| 天 | 日期 | 主题 | 硬闸门 |
|---|---|---|---|
| D1 | 11/04 | 环境/骨架/探针/最小垂直 | 构建、health、真实探针或 blocked、设备安装或 blocked、目标→步骤卡真实跑通 |
| D2 | 11/05 | 契约固化/完整文本/烹饪 | 真实计划 + Pydantic + 黄金样例 + 错误路径 |
| D3 | 11/06 | 步骤/进度/计时/提问/软件/修订 | 计划锁定、done/skipped 保留、计时重启、条件 PATCH |
| D4 | 11/07 | 媒体/图片/短片/摄影 | 证据/时间戳/限制、无音频/精确评分 |
| D5 | 11/08 | 运镜/Canvas/咖啡 | 结构化 spec、单变量、口味仅用户 |
| D6 | 11/09 | 参考/四领域/加固/彩排 | 四领域真实端到端、超限/注入拒绝、密钥扫描 |
| D7 | 11/10 | 发布/材料 | 干净安装、视频≤3min、提交包完整 |
| 缓冲 | 11/11–11/16 | 修复/材料定稿 | 11/16 包就绪；11/17 前用户提交 |

比赛：报名 11/5（用户手工）；官网标题截止 11/18 vs 赛程 11/17，**按 11/17 前准备**；不擅自报名/提交/发布商店。

## 8. 红线（违反即停止）

1. **不伪造**：模型结果、测试、构建、截图、码道证据、GitHub 推送、设备可用性。
2. **不泄密**：Key 只在服务端 `.env`；不进 APK/BuildConfig/Gradle/Git/日志/截图/视频/PPT；不打印环境变量。
3. **不缩范围**：四领域、参考教程、照片/短片反馈、运镜动画、配方历史、成果记录全部保留；只可削减视觉打磨/附加动画类型。
4. **不越权**：不安装系统组件/大型环境、不改系统 `JAVA_HOME`/PATH、不公网部署、不购买服务、不发布商店、不报名/提交，除非用户明确批准。
5. **不误导**：图片不判断内部温度/食用安全；不从照片推断口味；稀疏帧不给精确评分；无语音能力不伪造转写；用户点下一步≠模型验证完成。
6. **不静默失败**：断网/超时/限流/坏 JSON/媒体失败必须有明确状态与重试；不得返回假结果。
7. **不篡改历史**：有进度时禁止全量重生成；done/skipped 不可改；修订需版本检查与用户确认。
8. **不截断冒充完整**：参考资料超 20,000 字符拒绝，不静默截断。

## 9. 首阶段报告要求

按 `docs/CODEARTS_PROMPTS.md` 的“阶段报告模板”输出：

- 修改文件；实际命令/退出码/关键输出；测试（真实 vs mock 分开）；设备/截图或 BLOCKED 原因；模型探针（模型名/耗时/状态，脱敏）；逐项 PASS/BLOCKED；未验证项；证据路径；需要用户批准/提供的事项；是否暂停。

**没有真实证据的“完成”一律视为未完成。**

## 10. 当前文档状态与下一步

- 文档已覆盖 CC_TASK 的 8 项结构；`CODEX_DOCUMENT_REVIEW.md` 的 R1–R5 与补充项已修复，并经 2026-11-04 第二轮只读一致性审计复核（残留项已修正，含产品 7.1/AC-08 的写盘前二次检查与提交窗口并发验收；见 `docs/README.md` 第 6 节）。
- 尚未创建应用源码、Gradle 工程、服务端实现、venv、AVD、Git 提交或 GitHub 推送。
- 下一步：用户审阅文档并确认；确认后再把 P0 交给码道。首日复测环境，真实探针/设备不可用则如实 BLOCKED，不进入假成功。
