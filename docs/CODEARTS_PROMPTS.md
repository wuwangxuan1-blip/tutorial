# 码道 Agent Space 分阶段提示词

> 用法：**一次只发一个阶段**。每个阶段先读规格、再实现、再自测、再报告、再暂停。不要在一个 Prompt 里要求“一次做完整个 App”。
> 本文件是提示词模板，不是应用代码；当前文档阶段不调用码道、不执行这些任务。
> 所有阶段共同遵守：不伪造模型结果/测试/截图/证据；不在 APK、Git、日志、截图放 Key；不改系统 `JAVA_HOME`/PATH；不安装大型环境或系统组件，除非用户明确批准；不发布商店、不报名/提交比赛。

## 0. 通用前置（每个阶段都适用）

把下面这段放在每个阶段 Prompt 的开头，或要求码道先读：

```text
你是本项目的实现 Agent。开始前必须按顺序阅读：
1) PROJECT_PLAN.md（项目主入口与红线）
2) docs/PRODUCT_REQUIREMENTS.md（功能与验收）
3) docs/API_CONTRACT.md（唯一接口契约）
4) docs/CODING_STANDARDS.md（实现规范）
5) docs/IMPLEMENTATION_PLAN.md 中本阶段对应章节
6) docs/CODEARTS_PROMPTS.md 中本阶段 Prompt 与报告模板
7) START_CODEARTS.md（证据与暂停要求）

工作目录：outputs/tutorial-coach。
只实现本阶段范围；不要重写其他阶段，不要改契约字段/错误码；发现规格冲突先停下报告，不要自行“简化”。
不得伪造任何命令输出、测试结果、模型响应、截图或 CodeArts 使用痕迹。
不得把 Key 写入源码、BuildConfig、Gradle、Git、日志、截图、演示或聊天。
不得修改系统 JAVA_HOME/PATH，不得安装大型环境/系统组件，除非用户明确批准。
每阶段结束必须：运行真实命令、保存证据到 codearts_proof/dayN/、更新 docs/IMPLEMENTATION_STATUS.md、按模板报告，然后暂停等待确认。
```

## P0：D1 环境复测、骨架、真实探针、最小链路

**目标**：证明工具链、服务端、模型探针的真实状态；打通“输入目标→澄清→真实计划→步骤卡”的最小垂直流程；建立可构建的 Android/服务端骨架和证据基线。**这是有边界的首阶段，不是完整 App。**

```text
【P0 / D1：环境复测、骨架、真实探针、最小垂直流程】

范围（只做这些）：
开工前先创建 `docs/IMPLEMENTATION_STATUS.md`，建立“CC_TASK 需求→文档→任务/阶段→状态（未开始/进行中/PASS/BLOCKED）→证据”的映射；后续每阶段更新，不事后补造。
A. 环境复测：按 docs/TECH_STACK.md 第 2/11 节与 START_CODEARTS.md 复测，不复制旧快照；创建/更新 docs/ENVIRONMENT.md。记录 Windows、JDK、JAVA_HOME、Gradle、AGP、SDK platforms/build-tools、adb 设备、AVD/系统镜像、ffmpeg/ffprobe、Python、依赖、DeepSeek Key 是否存在、Git/GitHub 状态。命令和真实输出写入 docs/ENVIRONMENT.md。
B. 本地 Git：按用户已表达的版本管理意愿，在 outputs/tutorial-coach 初始化本地仓库（若尚未初始化；若用户未确认则先询问），写 .gitignore，首次提交只含文档/配置/骨架；没有 remote/凭据时不要伪造 push，记录 GitHub: BLOCKED。
C. Android 骨架：单 module Kotlin + Jetpack Compose + Material3；MainActivity；最小目标输入/领域选择/澄清问题/计划页/步骤卡；设置/诊断页显示 /v1/health 结果；仅 INTERNET 权限；不接相机/存储权限；不写业务假数据。
D. 服务端骨架：FastAPI；GET /v1/health、GET /v1/capabilities；配置从环境变量/.env 读取（不打印值）；统一错误信封；数据目录；结构化日志（脱敏）。健康/能力接口不调用模型。
E. 最小垂直流程：POST /v1/sessions 创建会话并返回领域问题（问题可来自服务端规则库）→ POST /v1/sessions/{id}/answers → POST /v1/sessions/{id}/plan-jobs 真实模型生成 → GET /v1/jobs/{id} / GET /v1/sessions/{id}/plan；Android 能输入烹饪目标、回答至少 1 个问题、触发计划并看到简单步骤卡。无 Key/失败时显示 MODEL_NOT_CONFIGURED/错误，不显示假计划。不要实现完整计时/媒体/动画/配方/参考。
F. 探针：scripts/probe_deepseek.py 真实调用文本、图片、JSON mode、可选工具调用；输出脱敏 JSON 到 codearts_proof/day1/。无 Key 时输出 {"blocked":"NO_KEY"} 并以非零退出；不要写成功。图片探针必须用真实小图，记录模型原始状态/错误。
G. 构建/安装：用会话级 JAVA_HOME=JBR 21 构建；assembleDebug；有设备则安装/启动并截图；无设备/AVD 则记录 BLOCKED，不得声称安装成功。build-tools 先按项目配置；若 AGP 拒绝 36，记录错误并请求批准安装 35。
H. 证据与状态：codearts_proof/day1/ 保存 prompt、命令、构建日志、探针日志、健康检查输出、截图/设备状态；更新开工前建立的需求映射，并写 D1 的 PASS/BLOCKED。

禁止：
- 不实现完整计时/媒体/动画/配方/参考导入；这些留给后续阶段。
- 不用静态 JSON 冒充模型计划；不把 mock 测试写成真实探针成功。
- 不安装系统镜像/AVD/大型依赖；如需要，先报告并请求用户批准。
- 不推送 GitHub（除非用户已提供 remote 且认证可用；仍不得强推/改他人仓库）。
- 不读取/打印 Key 值或无关个人文件。

验收（逐项报告真实结果）：
1) gradlew --version：Gradle 8.9 + JVM 21.0.7（或记录实际差异）。
2) assembleDebug 成功且 APK 路径存在；安装/启动 PASS 或 BLOCKED（写明原因）。
3) /v1/health 200；无 Key 泄露；Android 诊断页能显示服务端状态。
4) 创建会话按领域返回 3–5 个问题；若条件已足够则直接 `ready`（记录原因）；离线/服务不可达有错误提示。
5) 最小垂直流程：设备上输入烹饪目标→回答澄清问题（若服务端已 `ready` 则记录原因）→真实模型计划→看到步骤卡；PASS 或 BLOCKED（无 Key/无设备/模型失败），不得用示例计划冒充。
6) 文本/图片/JSON 探针：真实 PASS，或明确 blocked/不支持；不得含糊。
7) 证据目录完整；IMPLEMENTATION_STATUS 有 PASS/BLOCKED/下一步。
8) 若用户已同意/已有 Git，本地 commit 完成；有 remote 则 push PASS，无 Git/remote 记 BLOCKED，不伪造。

结束：按“阶段报告模板”输出，然后暂停，等待用户确认。不要自动进入 P1。
```

## P1：D2 契约固化、完整文本流程、烹饪

**前置**：P0 已报告，用户确认进入。若 P0 的模型文本/JSON 闸门为 BLOCKED，先说明只能做契约/错误路径，真实计划闸门仍 BLOCKED；不要用假计划继续。

```text
【P1 / D2：契约固化 + 完整文本流程 + 烹饪】

必须先读：docs/API_CONTRACT.md 第 1–5、7、8 章；PRODUCT_REQUIREMENTS 第 3–7 章；IMPLEMENTATION_PLAN D2；CODING_STANDARDS 的 DTO/模型输出/测试章节。

边界：D1 已有“目标→澄清→计划→步骤卡”最小流程；本阶段只做契约对齐、完整字段/校验、两轮澄清、错误路径、提示词质量与测试，不重写流程、不扩展到计时/媒体。

实现：
1) 契约黄金样例：contracts/examples/ 下 session、questions、plan、job、error 的 JSON；服务端 Pydantic 与 Android kotlinx.serialization 双向解析测试。字段名/错误码严格按契约，不改名。
2) 服务端：POST /v1/sessions、POST /v1/sessions/{id}/answers、POST /v1/sessions/{id}/plan-jobs、GET /v1/sessions/{id}/plan、GET /v1/jobs/{id}；会话/条件/问题存储；Job 异步执行与轮询；模型 JSON mode；Pydantic 校验；一次修复重试；错误码 MODEL_NOT_CONFIGURED/MODEL_TIMEOUT/MODEL_RATE_LIMITED/MODEL_BAD_OUTPUT/MODEL_REFUSED。
3) 烹饪提示词：目标 + 条件 + 参考资料（本阶段可先不接参考）→ 结构化 Plan；每步严格用契约 Step 字段：title/instruction/why/duration_s/completion_criteria/safety（另含 phase/order 等，见 API_CONTRACT 3.5）；assumptions 列缺失条件；不要编造用户未提供的设备/食材。
4) Android：在 D1 页面基础上补齐两轮澄清、计划总览完整字段、基础步骤卡错误态（先不做完整计时/媒体/修订）；Job 轮询；模型错误/无 Key/超时 UI；不显示假计划。
5) 测试：契约双向、计划 Pydantic 校验、Job 成功/失败、非法 JSON、无 Key、超时映射；真实模型探针单独跑并保存日志（不放进默认 mock 测试）。
6) 烹饪演示目标“2 人份番茄鸡蛋面，30 分钟内，家用灶具”真实跑通；记录计划结构和完成标准。

禁止：
- 不实现媒体、运镜、配方、参考导入（后续阶段）。
- 不把 mock 计划提交为演示数据；无 Key/失败时 UI 必须明确，不得显示示例步骤冒充生成结果。
- 不让模型输出任意 HTML/代码；只接受契约字段。
- 不记录用户原文/Key 到 INFO 日志。

验收：
- 服务端 pytest 通过；Android testDebugUnitTest 通过；assembleDebug 成功。
- 真实模型调用生成计划并通过 Pydantic；日志含模型名/耗时/状态，不含 Key。
- 烹饪目标在设备上走通；无 Key/坏 JSON/超时均有明确 UI 和重试。
- 契约样例两端解析通过；计划步骤 3–15 个，均有可观察完成标准。
```

## P2：D3 步骤 UX、进度/计时/暂停/恢复、提问、软件、修订锁定

```text
【P2 / D3：步骤交互 + 进度/计时/暂停/恢复 + 提问 + 软件领域 + 修订锁定】

必须先读：PRODUCT_REQUIREMENTS P-05/P-06、状态机、AC-07/AC-08/AC-08b；API_CONTRACT 3.2.1（条件可空规则）、3.9（Revision）、4.3（进度/提问/条件）、4.5（修订）、5.3、8；CODING_STANDARDS 计时/计划锁定；IMPLEMENTATION_PLAN D3。

实现：
1) 服务端：PATCH /progress、POST /pause、/resume、/complete、/abandon；POST /ask；PATCH /conditions；POST /revision-jobs；POST /revisions/{id}/apply、/reject。以下会话内路径均以 `/v1/sessions/{id}` 为前缀（`/revisions/{id}` 实为 `/v1/sessions/{id}/revisions/{rid}`），完整定义以 API_CONTRACT 第 4 章为准。实现：
   - 用户点完成只写 self_reported，不自动标“模型已验证”。
   - 计时 anchor_elapsed_ms/saved_at_epoch_ms；暂停时禁止进度写入；恢复合并。
   - 条件 PATCH 严格按 3.2.1：省略=不变；非空=设置；null=清除非关键字段；空字符串非法；关键字段 null 原子 422；PATCH 不让 ready 退回 clarifying。
   - 有进度/当前步骤/计时器时 POST /plan-jobs → 409 PLAN_LOCKED；条件修订 feedback_id=null + request_reason，只改未完成步骤；done/skipped 不变。Job 写盘前二次检查 base_plan_version 与进度/计时器，提交窗口内出现进度则失败且不覆盖；应用时再检查 base_plan_version。
2) Android：完整步骤卡（上一步/下一步/暂停/恢复/计时/保存/退出）、提问面板、条件修改页、修订提案差异/应用/拒绝、证据标签、离线/错误横幅、本地进度缓存、进程死亡/旋转恢复、设备重启后计时确认且不出现负值。
3) 软件领域提示词/问题/演示任务（Windows 11 照片复制+按日期重命名）；命令只作为文本，不自动执行。
4) 测试：计时重启/暂停/恢复；条件省略/null/空串/关键字段；PLAN_LOCKED；条件修订保留 done/skipped；409 VERSION_CONFLICT；ask 45/60/75s 超时分层；保存/恢复。
5) 软件演示目标真实计划；不执行用户机器命令。

禁止：
- 不实现媒体反馈/运镜/配方（后续阶段）。
- 不在有进度时全量重生成或覆盖已完成步骤。
- 不把用户“下一步”当模型验证完成。
- 不用负计时/假保存掩盖重启问题。

验收：
- pytest + testDebugUnitTest + assembleDebug 通过。
- 设备上完成：步骤前进/后退、暂停/恢复、计时、杀进程恢复、条件修改、提问、修订应用/拒绝。
- 有进度时全量重生成返回 409；条件修订后 done/skipped 原样保留；条件 PATCH 边界与契约一致。
- 软件演示目标真实跑通，命令不自动执行。
```

## P3：D4 媒体、图片/短片反馈、摄影

```text
【P3 / D4：媒体上传 + 图片/短片反馈 + 摄影领域】

必须先读：PRODUCT_REQUIREMENTS P-07、四领域摄影行、媒体/证据/安全边界、AC-09/AC-10/AC-16；API_CONTRACT 3.7/3.8/3.11/4.4/4.7/7；CODING_STANDARDS 媒体/证据/ffmpeg；IMPLEMENTATION_PLAN D4。

实现：
1) 服务端：POST /v1/media（multipart）；POST /v1/sessions/{id}/feedback-jobs；GET /v1/feedback/{id}；图片 JPEG/PNG/WebP ≤10 MiB、最多 4 张；HEIC 转 JPEG；视频 MP4/MOV ≤30s/≤100 MiB、一次 1 段；ffprobe 校验；1 fps 抽样最多 8 帧（带时间戳）；运动估计 10 fps、最多 300 帧、320px 灰度，ffmpeg vidstabdetect/vmafmotion；无 OpenCV；音频不分析。
2) 反馈 Pydantic：observations 每条必须有 evidence（`media_id`；视频另带 `frame_index`/`timestamp_s`）；给 uncertainties/limitations；评估只能是 not_verified/likely_met/unclear/not_met；不自动改步骤完成。图片不能判断内部温度/食用安全；短片不编造精确评分；运动失败 motion_metrics=null + limitation。
3) 摄影提示词/问题/演示任务“手机环绕拍咖啡 8 秒”；本阶段摄影计划按契约返回 CameraMoveSpec（若暂不绘制动画，可 `visual_aid=null` 并明确提示），D5 完成 Canvas 播放；不得伪造动画/参数。
4) Android：Photo Picker、图片预览/压缩、视频选择与大小/时长预检、上传进度/重试、反馈页（证据缩略图/时间戳/局限/评估）、隐私提示；不做实时相机。
5) 测试：格式/大小/时长/数量、解码失败、证据缺失拒绝、音频 false、运动失败 null、上传重试、无假 Feedback。
6) 真实图片与短片反馈各跑一次，保存脱敏日志/截图；合成视频只用于技术测试，不作为“真实拍摄”演示。

禁止：
- 不把视频当图片直接发模型；不分析/转写音频；不提交 HEIC 原图给模型。
- 不从照片推断温度/安全/口味；不凭稀疏帧给 0–100 评分。
- 视觉探针失败仍要明确显示“模型视觉不可用”，不得用假观察填充。
- 不引入 OpenCV/大型依赖（除非用户批准；当前方案不需要）。

验收：
- pytest + testDebugUnitTest + assembleDebug 通过。
- 真实图片反馈有证据；短片反馈有时间戳/局限；媒体限制真实执行；超限明确错误。
- 无音频分析、无精确评分、无自动完成。
- 摄影演示目标真实计划+真实反馈，或明确 BLOCKED（不得假成功）。
```

## P4：D5 运镜 CameraMoveSpec/Canvas、咖啡配方

```text
【P4 / D5：结构化运镜 + Canvas 动画 + 咖啡配方/口味/单变量/历史】

必须先读：PRODUCT_REQUIREMENTS P-05 摄影/咖啡、AC-11/AC-12；API_CONTRACT 3.6/3.10/4.6/5.4；CODING_STANDARDS 动画/配方；IMPLEMENTATION_PLAN D5。

实现：
1) CameraMoveSpec：motion_type=camera_move|lens_zoom|orientation_only|static；shot_type=dolly_in/dolly_out/truck_left/truck_right/pan_left/pan_right/tilt_up/tilt_down/orbit_cw/orbit_ccw/zoom_in/zoom_out/static 的合法组合；归一化俯视坐标/路径点/时长/缓动/限制；Pydantic + Kotlin 校验；拒绝 NaN/越界/缺路径/类型不一致。
2) Android Canvas：画机位路径、主体、朝向/变焦区分；播放/暂停/重播；时间轴；不执行模型生成的代码/HTML/SVG。
3) 咖啡：Recipe/RecipeVersion/Tasting/Adjustment/History/Compare API + UI；用户手动 tasting 分数/描述；一次只改一个变量（服务端强校验 SINGLE_VARIABLE_REQUIRED）；base_version 冲突 409；历史只读；对比只展示参数/用户评分差异，不推断口味。
4) 咖啡提示词/问题/演示任务 V60 15g/225g/92°C/约2:30；设备缺失给替代提示，不编造参数。
5) 测试：CameraMoveSpec 合法/非法；动画播放状态；配方版本链/单变量/409/对比；照片不推断口味。

禁止：
- 不执行模型生成的动画代码；只渲染结构化 spec。
- 不从照片推断咖啡口味；不自动替用户打分。
- 不做多变量同时调整；不覆盖历史版本。
- 不把 2D 示意图说成 3D/真实镜头模拟。

验收：
- pytest + testDebugUnitTest + assembleDebug 通过。
- 摄影计划含合法 spec，动画可播放；非法 spec 被拒。
- 咖啡 v1→tasting→单变量调整→v2→history/compare 可用；单变量强校验；口味仅来自用户。
```

## P5：D6 参考教程、四领域端到端、加固、彩排

```text
【P5 / D6：参考教程 + 四领域端到端 + 故障注入 + 加固 + 彩排】

必须先读：PRODUCT_REQUIREMENTS 第 6 章参考边界/AC-15/AC-16；API_CONTRACT 3.12/4.7/7/8；CODING_STANDARDS 注入防护/秘密/日志/测试；IMPLEMENTATION_PLAN D6。

实现：
1) 参考教程：`POST /v1/references/text` 同步；`POST /v1/references/import-url` 与 `POST /v1/references/import-file` 异步（202 Job）；`GET/DELETE /v1/references/{id}`。支持 txt/md/pdf 文本层/docx/公开 http(s) 页面/图片（≤4 张）/视频（≤30s/≤100 MiB，抽帧）。
2) 边界：单条/合计 >20,000 字符拒绝（REFERENCE_TOO_LONG/REFERENCE_BUDGET_EXCEEDED），不截断；扫描 PDF 无文本层/登录页/付费墙/JS 渲染/视频平台链接/私网/重定向>3/页面>2 MiB 明确拒绝；不做 OCR/绕过登录/下载受保护内容；外部教程只作为资料，不作为系统指令（<reference_material> 包裹，冲突时以本产品规则/用户当前条件优先）。
3) 四领域演示任务全部真实端到端（烹饪/摄影/软件/咖啡）；记录/成果/历史可回查；参考教程在至少一个领域真实使用。
4) 故障注入：无 Key、401/402/429、超时、非法 JSON、媒体失败、服务重启、版本冲突、PLAN_LOCKED、条件 null、参考超长/SSRF/注入样例；所有失败有明确 UI/重试，不静默假结果。
5) 秘密/日志扫描：无 Key/.env/个人媒体/构建垃圾入库；日志脱敏；截图不含 Key；README 草稿。
6) Codex 审查；codearts_proof/day6/；IMPLEMENTATION_STATUS 更新。

禁止：
- 不实现 OCR/验证码/登录绕过/反爬绕过；不抓取非公开内容。
- 不静默截断资料；不把参考资料当系统指令。
- 不在 D6 加新功能；发现阻断回到对应阶段。
- 不把合成/静态素材当四领域真实演示。

验收：
- 全量 pytest + testDebugUnitTest + assembleDebug 通过。
- 四领域各一条真实演示；参考资料真实使用；超限/SSRF/注入/扫描件被正确拒绝。
- 故障注入全部有恢复路径；密钥扫描通过；Codex 阻断项清零或记录。
```

## P6：D7 发布与比赛材料

```text
【P6 / D7：APK、README、脚本、视频、PPT、证据、提交包】

必须先读：COMPETITION_CHECKLIST.md；IMPLEMENTATION_PLAN D7；PRODUCT_REQUIREMENTS AC-20；START_CODEARTS 证据要求。

实现：
1) 干净构建 debug APK；干净安装/启动截图；记录 commit hash。
2) README：依赖、服务端启动、.env 配置（不写真实 Key）、APK 安装、adb reverse、四领域演示、限制（APK 非独立联网/无实时相机/无音频分析/2D 运镜示意）、隐私、排错。
3) 脚本：setup-server.ps1、run-server.ps1、build-apk.ps1、install-apk.ps1、verify-submission.ps1；不嵌 Key；不修改系统设置。
4) submission/：PPT（≤10 页）、3 分钟视频（≤3:00）、源码/依赖说明、codearts_proof、开源组件/许可证、部署运行、码道总结；证据脱敏。
5) 提交前检查：无 Key/.env/keystore/个人媒体/构建垃圾；APK 存在；视频时长；README 与实现一致；四领域演示可用；Git 标签/commit（有 remote 则推送）。
6) 最终报告：材料清单、真实检查命令/结果、未验证项、人工待办（报名/官网日期复核/最终提交）。

禁止：
- 不报名、不提交比赛、不发布应用商店、不购买服务。
- 不伪造视频/截图/码道痕迹；不把 mock 当演示。
- 不在发布阶段改核心功能；只修阻断/文案/演示问题。
- 不把 Key 放进 APK/README/视频/PPT/日志。

验收：
- 干净安装/启动；四领域演示可用；视频≤3分钟；PPT/README/证据齐全。
- verify-submission.ps1 真实通过；无秘密/垃圾；提交包 11/16 就绪。
- 报告明确：已提交/未提交（应由用户手工完成）、日期冲突、剩余风险。
```

## 阶段报告模板（每阶段结束必须使用）

```text
【阶段 N 报告】

1) 阶段/日期/commit：
2) 修改文件（路径 + 一句话）：
3) 运行命令与真实结果（命令、退出码、关键输出；不要贴 Key/用户原文）：
4) 测试结果（pytest/Android/手工；mock 与真实探针分开写）：
5) 设备/安装/截图（设备型号或 BLOCKED 原因；截图路径）：
6) 模型探针（文本/图片/JSON/工具调用；模型名、耗时、状态；失败原文脱敏）：
7) 验收项逐条 PASS/BLOCKED（对应本阶段验收编号）：
8) 未验证/未完成/已知问题：
9) 证据路径（codearts_proof/dayN/...）：
10) 下一步建议 + 需要用户批准/提供的事项：
11) 是否暂停等待确认：是（默认）
```

## Codex 审查请求模板

```text
请审查阶段 N 的实现，重点：
1) 是否严格遵循 docs/API_CONTRACT.md 的字段/端点/错误码/状态机；有无契约漂移。
2) 是否违反证据诚实：假计划/假反馈/mock 冒充真实/未验证却标 PASS/用户点下一步当模型验证。
3) 计划锁定/条件 PATCH/参考资料不截断/超时分层/计时重启是否按规格实现。
4) 媒体限制、视频抽帧/运动局限、无音频分析、食物安全/口味边界。
5) Key/日志/截图/Git 是否泄露；错误路径是否静默失败。
6) 测试是否覆盖阻断项；CodeArts 证据是否真实完整。
输出：阻断项（必须修）、建议项（可延后）、未验证项；不要改代码，只给审查结论。
```

## 回滚与暂停规则

- 任一阶段出现契约冲突/无法真实通过闸门：**停止扩展**，在 `IMPLEMENTATION_STATUS.md` 记录 `BLOCKED`、复现命令、错误日志、影响范围；不要用假数据绕过。
- 代码回滚用本地 Git：保留失败证据后 `git revert`/回到上一绿色 commit；不要 `reset --hard` 丢弃未提交证据。
- 模型/设备/Key 阻塞：可继续不依赖该能力的契约/错误路径/UI，但相关验收保持 `BLOCKED`；演示不得声称已完成。
- 每阶段结束默认暂停；只有用户明确说“进入下一阶段”才继续。
- 比赛报名/提交、GitHub 推送、安装系统组件/大型依赖、公网部署：必须用户明确批准，不得由 Agent 自行执行。

## 阶段与七天映射

| Prompt | 计划日 | 主题 | 硬闸门 |
|---|---|---|---|
| P0 | D1 | 环境/骨架/探针/最小链路 | 构建、health、真实探针或 blocked、设备安装或 blocked |
| P1 | D2 | 契约/文本/烹饪 | 真实计划 + Pydantic + 错误路径 |
| P2 | D3 | 步骤/进度/计时/提问/软件/修订 | 计划锁定、done/skipped 保留、计时恢复 |
| P3 | D4 | 媒体/图片/短片/摄影 | 证据、时间戳、限制、无音频/精确评分 |
| P4 | D5 | 运镜/Canvas/咖啡 | 结构化 spec、单变量、口味仅用户 |
| P5 | D6 | 参考/四领域/加固/彩排 | 四领域真实端到端、注入/超限拒绝、密钥扫描 |
| P6 | D7 | 发布/材料 | 干净安装、视频≤3min、提交包完整 |
