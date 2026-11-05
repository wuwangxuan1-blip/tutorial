# D2 共享契约验证

## 样例

`contracts/examples/` 由服务端 Pydantic 与 Android kotlinx.serialization 共同读取：

- `session_create_request.json`
- `session.json`
- `questions.json`
- `plan_cooking.json`
- `job.json`
- `job_failed.json`
- `error_version_conflict.json`

样例来源与契约观察见 `contracts/README.md`。

## 服务端

命令：

```bash
cd server
.venv/Scripts/python.exe -m pytest -q
```

结果：**47 passed**。

`server/tests/test_contract_examples.py`（8 项）覆盖：

- 创建请求、Question[]、Session、Plan、Job 成功/失败、错误信封的 Pydantic 解析；
- 响应样例 `model_dump(mode="json")` 与原始 JSON 等价；
- ID 前缀、枚举、可空值、步骤数量、完成标准；
- 未知 Conditions 字段、非法枚举、空字符串、非法 phase、空 completion_criteria 被拒绝。

## Android

命令：

```bash
cd android
export JAVA_HOME=<JDK21>
./gradlew --no-daemon :app:testDebugUnitTest --console=plain
```

结果：**19 passed**（`ContractExamplesTest` 6 项、DtoTest 3、ErrorMapperTest 5、PlanValidatorTest 4、PlanViewModelTest 1）。

`ContractExamplesTest` 从测试资源读取同一批文件；`app/build.gradle.kts` 的 test sourceSet 指向 `../contracts/examples`，没有复制样例。测试覆盖反序列化、重新编码、枚举/可空值、Job error 嵌套、错误 details。

## 契约观察

- §3.3 Session 示例省略 `progress.evidence_levels`，但 §3.4 定义该字段；样例包含空对象。
- §3.14/§4.8 成功 Job 示例使用 `stage="done"`；D2 服务端已对齐为 `"done"`，Android 显示“完成”。
- `Step.visual_aid` 完整 camera_move 校验属于 §3.6/D5；本阶段烹饪计划使用 `null`，未扩展运镜。
- `Job.error` 为完整错误信封，样例与双端 DTO 均按嵌套结构验证。
- 未修改契约字段名或错误码。