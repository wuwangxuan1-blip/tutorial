# 实践陪练（tutorial-coach）文档导航

> 本目录是产品、技术、契约、规范、实施计划与码道交接的唯一规格源。
> 文档基线：2026-11-04；当前阶段**只写文档，不写应用代码**。
> 项目根目录的 [`PROJECT_PLAN.md`](../PROJECT_PLAN.md) 是码道交接主入口；本文件是详细导航。

## 1. 阅读顺序

| 顺序 | 文档 | 先读什么 | 用途 |
|---|---|---|---|
| 1 | [PRODUCT_REQUIREMENTS.md](PRODUCT_REQUIREMENTS.md) | 定位、四领域、AC | 确认做什么/不做什么、怎么验收 |
| 2 | [TECH_STACK.md](TECH_STACK.md) | 选型、版本、环境、构建/部署 | 确认技术方案与本机限制 |
| 3 | [API_CONTRACT.md](API_CONTRACT.md) | 通用约定、模型、端点、错误码、状态机 | 前后端唯一契约；写代码前必须读 |
| 4 | [CODING_STANDARDS.md](CODING_STANDARDS.md) | 模块边界、协程、模型输出、安全、测试、Git | 实现规范与审查清单 |
| 5 | [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) | D1–D7、闸门、命令、风险 | 七天执行与每日验收 |
| 6 | [CODEARTS_PROMPTS.md](CODEARTS_PROMPTS.md) | P0–P6、报告模板、回滚 | 逐阶段交给码道；一次一个 Prompt |
| 7 | [COMPETITION_CHECKLIST.md](COMPETITION_CHECKLIST.md) | 日期冲突、材料、视频、提交检查 | 比赛材料与提交准备 |
| 8 | [RISK_REGISTER.md](RISK_REGISTER.md) | P0 风险、人工待办、验证命令 | 风险跟踪与失败处理 |
| 9 | [CODEX_DOCUMENT_REVIEW.md](CODEX_DOCUMENT_REVIEW.md) | R1–R5 与补充项 | 首轮审查历史记录；修复状态见第 6 节 |

**角色分工**

- **用户**：确认产品名/部署/报名提交；提供 Key（仅本地）、真机、真实演示素材；最终审阅。
- **Claude Code（本阶段）**：Plan 模式整理规格与文档；不写应用代码、不调用码道、不安装、不提交。
- **码道 Agent Space**：按 `CODEARTS_PROMPTS.md` 分阶段编写主要代码，保存生成/调试/重构/Prompt 证据。
- **Codex**：规划协调、代码审查、契约/证据核查；不把其他工具代码记为码道。

## 2. 文档地图

```text
PROJECT_PLAN.md                  # 码道主入口：目标/红线/栈/闸门/文档索引
docs/
  PRODUCT_REQUIREMENTS.md        # 用户故事、页面、四领域、状态机、AC
  TECH_STACK.md                  # 选型比较、版本、环境、构建/部署、数据流
  API_CONTRACT.md                # v1 端点/模型/示例/错误/超时/状态机
  CODING_STANDARDS.md            # Kotlin/服务端/模型/媒体/安全/测试/Git
  IMPLEMENTATION_PLAN.md         # D1–D7、命令、闸门、追踪矩阵
  CODEARTS_PROMPTS.md            # P0–P6 可复制 Prompt + 报告/审查模板
  COMPETITION_CHECKLIST.md       # PPT/视频/README/证据/许可证/提交检查
  RISK_REGISTER.md               # 风险、人工待办、验证、关闭标准
  CODEX_DOCUMENT_REVIEW.md       # 首轮审查记录（历史）
  README.md                      # 本导航
  ENVIRONMENT.md                 # D1 由码道创建：真实环境复测
  IMPLEMENTATION_STATUS.md       # D1 由码道创建：需求→任务→PASS/BLOCKED 映射
contracts/examples/              # 黄金样例（后续由码道创建）
codearts_proof/dayN/             # 每阶段真实证据（后续由码道创建）
submission/                      # 比赛提交包（后续 D7 创建）
```

## 3. 关键决策摘要（详见各文档）

- **平台**：原生 Android，Kotlin + Jetpack Compose + Material3；不是 Web/PWA/WebView。
- **服务端**：Python 3.12 + FastAPI + uvicorn；本地 `127.0.0.1:8000`；开发/比赛用 `adb reverse`。
- **模型**：DeepSeek 官方 API；Key 仅服务端；模型名环境变量；主流程 JSON mode + Pydantic + 一次修复；不依赖工具调用。
- **媒体**：图片 JPEG/PNG/WebP ≤10 MiB、最多 4 张；视频 MP4/MOV ≤30s/≤100 MiB、一次 1 段；1 fps 最多 8 帧；音频不分析；运动指标有连续帧/局限。
- **证据**：`none/self_reported/media_submitted/model_observed/measured/not_verifiable`；用户点下一步 ≠ 模型验证完成。
- **计划锁定**：有进度/当前步骤/计时器时禁止全量重生成（409 `PLAN_LOCKED`）；条件修订只改未完成步骤；完成/跳过不可改。
- **参考资料**：单条/合计 ≤20,000 字符；超限拒绝（`REFERENCE_TOO_LONG`/`REFERENCE_BUDGET_EXCEEDED`），不截断。
- **版本**：Gradle 8.9 + AGP 8.7.3（本机缓存）+ JBR 21.0.7；compileSdk/targetSdk 35、minSdk 26；build-tools 35 缺失，先试 36，失败需批准装 35。
- **当前阻塞**：无 DeepSeek Key；无 AVD/系统镜像/真机；无 GitHub remote/凭据；tutorial-coach 未初始化 Git。首日必须复测。

## 4. 术语表

| 术语 | 含义 |
|---|---|
| 会话 Session | 一次目标练习的容器：目标、条件、计划、进度、媒体、记录 |
| 条件 Conditions | 材料/器具/版本/基础/时间/人数/份量/偏好等领域字段 |
| 计划 Plan | 准备清单、步骤、预计时间、完成标准、安全提示；有 `plan_version` |
| 步骤 Step | 可执行单元；`not_started/in_progress/done/skipped`；完成标准必须可观察 |
| Job | 异步任务：计划生成/参考导入/反馈/修订；状态 `queued/running/succeeded/failed/cancelled/expired` |
| 证据等级 | 观察来源：用户自述/媒体/模型观察/测量/不可验证 |
| 评估 | `not_verified/likely_met/unclear/not_met`；不等于步骤完成 |
| Revision | 基于反馈/条件的修订提案；应用前用户确认；版本冲突 409 |
| CameraMoveSpec | 结构化运镜参数（机位/朝向/路径/时长/缓动）；Canvas 绘制，不执行代码 |
| RecipeVersion | 不可变配方版本；tasting 只来自用户；一次只改一个变量 |
| 黄金样例 | `contracts/examples/` 的 JSON；前后端双向解析测试 |
| 闸门 Gate | 每日必须真实通过的验收；失败写 `BLOCKED`，不得假成功 |

## 5. 需求追踪入口

- 产品验收：`PRODUCT_REQUIREMENTS.md` 第 10 章 AC-01–AC-20（含 AC-08b/AC-16b）。
- 阶段映射：`IMPLEMENTATION_PLAN.md` 第 7 章需求追踪矩阵。
- 比赛材料：`COMPETITION_CHECKLIST.md` 第 9 章提交检查表。
- 风险/人工待办：`RISK_REGISTER.md` 第 6 章。

## 6. 审查修复索引（CODEX_DOCUMENT_REVIEW）

| 审查项 | 问题 | 修复位置 | 状态 |
|---|---|---|---|
| R1 | 条件 PATCH 语义矛盾 | `API_CONTRACT.md` 3.2.1/4.3；`PRODUCT_REQUIREMENTS.md` AC-08b；`CODING_STANDARDS.md` 测试 | 已修（2026-11-04 复核：422 口径统一） |
| R2 | 参考资料截断不一致 | `API_CONTRACT.md` 3.12/4.7/7；`PRODUCT_REQUIREMENTS.md` 6/AC-16；`CODING_STANDARDS.md`；`TECH_STACK.md` 数据流 | 已修：超限拒绝，不截断 |
| R3 | 全量重生成绕过已完成步骤 | `API_CONTRACT.md` 4.3/5.3；`PRODUCT_REQUIREMENTS.md` 7.1/AC-08；`CODING_STANDARDS.md` | 已修：`PLAN_LOCKED` + 创建/写盘双重检查 + 条件修订 |
| R4 | 缺实施计划/码道提示词 | `IMPLEMENTATION_PLAN.md`；`CODEARTS_PROMPTS.md` | 已补 |
| R5 | 本地服务被称“已接受限制” | `TECH_STACK.md` 部署节；`PRODUCT_REQUIREMENTS.md` 部署边界 | 已改为待用户确认 |
| 补充 | 已完成步骤可改/超时不一致/计时重启 | API/产品/规范/实施计划 | 已修：完成/跳过不可改；超时分层；计时重启检测 |

2026-11-04 第二轮只读一致性审计发现的残留已在同日修正：健康检查示例改为 `degraded`；P1 步骤字段改用 `duration_s`/`completion_criteria`；D1 增加 `requirements.txt` 生成步骤；`plan-jobs` 写盘前二次检查贯穿产品 7.1/AC-08、实施计划、提示词和测试；计时恢复改用锚点；P5 参考端点补全；问题数统一为 3–5；修订请求字段统一为 `request_reason`；比赛素材截止与 D4 区分；依赖文件名、风险超时摘要和项目现状已校正。

## 7. 文档维护规则

1. `API_CONTRACT.md` 是唯一契约源；改字段/端点/错误码必须同步产品、规范、计划、Prompt 与黄金样例。
2. 任何“未验证”必须显式写；不得用“应该/大概/已支持”替代真实探针。
3. 不写空泛的待定项；未决事项必须写责任/截止/失败处理。
4. 文档日期用绝对日期（如 2026-11-04），不写“今天/下周”。
5. 不在文档/样例/截图放真实 Key、账号、个人媒体。
6. 当前阶段只改文档；应用代码由码道按 Prompt 分阶段实现。

## 8. 变更记录

| 日期 | 变更 |
|---|---|
| 2026-11-04 | 初版导航；补 IMPLEMENTATION_PLAN/CODEARTS_PROMPTS/COMPETITION_CHECKLIST/RISK_REGISTER；记录 R1–R5 修复索引 |
| 2026-11-04 | 第二轮只读一致性复核：修正健康检查示例、P1 步骤字段、D1 依赖生成、计划写盘前二次检查、计时锚点恢复、参考端点、问题数、`request_reason`、素材截止等 |
| 2026-11-04 | 第三轮复核：产品 7.1/AC-08 补写盘前二次检查与提交窗口并发验收 |
