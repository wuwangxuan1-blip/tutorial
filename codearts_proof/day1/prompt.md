# P0 / D1 码道执行 Prompt（脱敏）

用户要求：严格依据项目文档只执行第一阶段 P0，完成后交给 Codex 审查。关键约束：

- 先完整阅读 PROJECT_PLAN、PRODUCT_REQUIREMENTS、TECH_STACK、API_CONTRACT、CODING_STANDARDS、IMPLEMENTATION_PLAN D1、CODEARTS_PROMPTS 通用前置/P0/报告模板、START_CODEARTS、REPOSITORY_SETUP。
- 建立 `docs/IMPLEMENTATION_STATUS.md` 与 `docs/ENVIRONMENT.md`；环境必须本次复测，不复用规划快照。
- 建立 Kotlin + Jetpack Compose Android 工程与 Python FastAPI 服务端。
- 实现健康检查、能力接口、配置加载、统一错误处理、脱敏日志。
- 验证 DeepSeek 文本、图片、JSON 输出，保存真实探针结果。
- 打通“输入烹饪目标 → 澄清条件 → 真实模型计划 → 步骤卡”；无设备/无 Key 必须明确 BLOCKED，不得用静态计划冒充。
- 构建 debug APK；无可用设备则明确标记 BLOCKED。
- 证据保存到 `codearts_proof/day1/`；不提交 `.env`、个人媒体、运行数据或未脱敏证据。
- 发现文档冲突先报告；不提前实现计时/媒体/运镜/配方/参考导入。
- 结束时按阶段报告模板汇报，暂停等待 Codex 审查。

本次未使用任何静态示例计划作为演示；`vertical_flow.json` 的计划来自真实 DeepSeek 调用。