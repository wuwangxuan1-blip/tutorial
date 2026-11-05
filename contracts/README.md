# 共享契约样例（P1/D2）

这些样例是服务端 Pydantic 与 Android kotlinx.serialization 的共同输入，来源为 `docs/API_CONTRACT.md`：

- `session_create_request.json`：§4.3 `POST /v1/sessions` 请求
- `session.json`：§3.3 Session（含 §3.1 Question、§3.4 Progress）
- `questions.json`：§3.1 Question[]（当前会话的澄清问题）
- `plan_cooking.json`：§3.5 Plan + Step
- `job.json`：§3.14 Job / §3.15 Job result / §4.8 成功轮询示例
- `job_failed.json`：§3.14 Job.error 的完整错误信封
- `error_version_conflict.json`：§1.2 错误信封

## 双端测试

- 服务端：`server/tests/test_contract_examples.py` 用 Pydantic 解析每个样例，并把响应样例序列化回等价 JSON。
- Android：`android/app/src/test/java/com/tutorialcoach/app/data/ContractExamplesTest.kt` 从测试资源读取同一批文件，反序列化后重新编码，再校验枚举、可空值和错误格式。
- 测试资源目录通过 `android/app/build.gradle.kts` 指向本目录，避免复制样例。

## 已知契约观察（不单方面改字段/错误码）

1. §3.3 的 Session 示例省略了 `progress.evidence_levels`，但 §3.4 明确定义该字段。样例按 §3.4 补齐为空对象；服务端/Android 均允许空对象。
2. §3.14/§4.8 的成功 Job 示例使用 `stage="done"`，P0 服务端曾返回 `stage="succeeded"`。`stage` 是自由字符串（≤40 字），不是枚举；D2 起服务端对齐为 `"done"`，Android 同时显示为“完成”。
3. §3.5 的 `Step.visual_aid` 只允许 timeline / ratio_table / camera_move 三类；D2 烹饪计划样例使用 `null`。完整 camera_move 校验属于 §3.6 与 D5 运镜阶段，不在本阶段实现。
4. `Job.error` 使用完整错误信封（`{"error": {...}}`），不是只放 ErrorDetail；`job_failed.json` 明确该嵌套结构。
5. 样例只覆盖 P1/D2 的文本流程；摄影/反馈/修订/配方/媒体/参考资料样例按 §9.1 在后续阶段补齐。

上述均未修改契约字段名或错误码；若后续实现与契约冲突，应同时更新契约、样例和两端测试。