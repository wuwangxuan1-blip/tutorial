# D2 命令与真实结果

| 命令 | 结果 |
|---|---|
| `server pytest -v` | **47 passed**（含契约 8、模型错误 8、修复 6、两轮澄清/跳过 2、Job 失败 2） |
| `android ./gradlew --no-daemon :app:testDebugUnitTest` | **BUILD SUCCESSFUL**；21 项，0 失败 |
| `android ./gradlew --no-daemon :app:assembleDebug` | **BUILD SUCCESSFUL**；APK 约 11 MB |
| `git ls-files -s android/gradlew` | `100755` |
| `scripts/vertical_flow_day2.py`（真实模型） | 两轮澄清→ready→Job succeeded；5 步；30.837 s / 5196 tokens；stage=done |
| 真机 `adb install -r` | Success |
| 真机两轮澄清 | 首轮 5 问只答 2 项 → 第二轮 3 问 → 答必填/跳过可选 → ready |
| 真机真实计划 | 27.079 s / 4682 tokens；5 步；6 条假设；准备清单/安全提示/步骤卡 1/5→2/5 |
| 契约样例双端 | 服务端 8 项 + 安卓 6 项通过，读取同一 `contracts/examples/` |
| `git push origin main` | 本轮修复提交待推送（前序 `8c5054d..e268dfe`） |
| 复审修复 | 见 `review_fix.md`；限流/非法 JSON/过敏提示测试 |
| `git push origin main`（复审修复） | PASS：`2d232e2..741b2e4`；未强推 |

说明：失败路径（无 Key/429/超时/非法 JSON/结构失败/拒绝）使用 httpx MockTransport/假模型和隔离 ASGI 应用，不是真实付费调用；真实模型只用于成功计划和真机流程。