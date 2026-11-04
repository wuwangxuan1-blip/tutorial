# D1 命令与真实结果

| 命令 | 结果 |
|---|---|
| `java -version`（默认） | Java 25.0.2；Gradle 8.9 不可用 JDK 25 |
| `D:\Java\ideaIU-2025.2.win\jbr\bin\java.exe -version` | JBR 21.0.7 |
| `bash ./gradlew --version`（标准 Wrapper，会话 JAVA_HOME=JBR21） | PASS：Gradle 8.9；Launcher JVM 21.0.7；见 `gradle_version.txt` |
| Codex 复审环境 `gradlew.bat :app:testDebugUnitTest :app:assembleDebug` | `BUILD SUCCESSFUL in 27s`（2026-11-04T15:58Z）；旧源码 APK；见 `android_test_results.txt` |
| `bash ./gradlew --no-daemon :app:testDebugUnitTest`（第三轮） | PASS：`BUILD SUCCESSFUL in 15s`，12 项，0 失败；见 `android_test_round3.log` |
| `bash ./gradlew --no-daemon :app:assembleDebug --rerun-tasks`（第三轮） | PASS：`BUILD SUCCESSFUL in 28s`，35 任务全部执行；APK 约 10 MB；见 `android_build_round3.log` |
| `:wrapper --gradle-version 8.9 --no-validate-url --gradle-distribution-sha256-sum ...` | 成功生成标准 Wrapper；官方 URL/SHA-256 见 `gradle/wrapper/gradle-wrapper.properties` |
| `adb devices -l` | 空列表，无设备；见 `device_status.txt` |
| `emulator -list-avds` | 无 AVD |
| `server/.venv/Scripts/python.exe -m pytest -v` | PASS：21 项；见 `server_pytest.log` |
| `server/.venv/Scripts/python.exe scripts/probe_deepseek.py` | PASS：文本/JSON/图片；见 `model_probe.json` |
| `server/.venv/Scripts/python.exe scripts/vertical_flow.py` | PASS：真实模型计划 4 步；见 `vertical_flow.json`、`vertical_flow.log` |
| `curl/ASGI GET /v1/health` | 200，`status=ok`，无 Key；见 `health.json` |
| `POST /v1/sessions`（烹饪，无初始条件） | 201，`clarifying`，5 个问题；见 `session_create.json` |
| `git push origin main` | PASS：`ab6996a..bcd3cc9 main -> main`；随后文档提交 `bcd3cc9..4798f2f main -> main`；远程 main 已核验 |

说明：本沙箱禁止本地回环连接，因此 Web 测试与真实垂直流程使用 `httpx.ASGITransport` 在进程内驱动同一 FastAPI 应用（middleware/路由/序列化/异常处理全部生效），不使用假响应。真实 DeepSeek 调用通过外网完成，结果见探针与垂直流程证据。