# D2 命令与真实结果

| 命令 | 结果 |
|---|---|
| `server pytest -v` | **44 passed**（含契约 8、模型错误 8、修复 6、两轮澄清/跳过 2、Job 失败 2） |
| `android ./gradlew --no-daemon :app:testDebugUnitTest` | **BUILD SUCCESSFUL**；19 项，0 失败 |
| `android ./gradlew --no-daemon :app:assembleDebug` | **BUILD SUCCESSFUL**；APK 约 11 MB |
| `git ls-files -s android/gradlew` | `100755` |
| `scripts/vertical_flow_day2.py`（真实模型） | 两轮澄清→ready→Job succeeded；5 步；33.509 s / 5315 tokens；stage=done |
| 真机 `adb install -r` | Success |
| 真机两轮澄清 | 首轮 5 问只答 2 项 → 第二轮 3 问 → 答必填/跳过可选 → ready |
| 真机真实计划 | 27.079 s / 4682 tokens；5 步；6 条假设；准备清单/安全提示/步骤卡 1/5→2/5 |
| 契约样例双端 | 服务端 8 项 + 安卓 6 项通过，读取同一 `contracts/examples/` |
| `git push origin main` | PASS：`8c5054d..e268dfe`；未强推 |

说明：失败路径（无 Key/429/超时/非法 JSON/结构失败/拒绝）使用 httpx MockTransport/假模型和隔离 ASGI 应用，不是真实付费调用；真实模型只用于成功计划和真机流程。