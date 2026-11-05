# codearts_proof/day2 索引（P1/D2）

| 文件 | 内容 |
|---|---|
| `contract_validation.md` | 共享契约样例双端验证与契约观察 |
| `error_paths.md` | 无 Key/限流/超时/非法 JSON/结构失败/拒绝/幂等/恢复测试矩阵 |
| `vertical_flow.json` | 真实模型两轮澄清→计划摘要（5 步、8 条假设、stage=done） |
| `vertical_flow.log` | 真实流程脱敏日志 |
| `plan_cooking_real.json` | 真实模型计划完整 JSON |
| `health.json` | 流程开始时 `/v1/health` |
| `server_pytest.log` | 服务端 47 项测试结果（P1 复审轮；P2/P3 轮 48 项见 `review_fix_device.md`） |
| `android_test.log` | 安卓单测输出 |
| `android_test_results.txt` | 安卓 21 项测试分套件统计 |
| `android_build.log` | debug APK 构建输出 |
| `android_apk_info.txt` | APK 大小、包名、版本、SDK 核验 |
| `device_verification.md` | 真机两轮澄清、含假设计划、步骤卡记录 |
| `device_status.txt` | adb 设备状态 |
| `device_server_full.log` | 真机流程对应服务端脱敏日志 |
| `device_plan_cooking.json` | 真机最新计划 JSON（生成于过敏提示泛化前） |
| `review_fix.md` | P1 复审三项修复与测试证据 |
| `review_fix_device.md` | P2/P3 复审修复、48 项服务端测试、21 项安卓测试与真机复核（测试模型替身） |
| `secret_scan_p2p3.json` | P2/P3 轮提交前密钥扫描（191 文件、0 匹配、clean） |
| `git_status.txt` | P1 复审修复提交与推送 SHA 核验 |
| `git_status.txt` | D2 提交与推送 SHA 核验 |
| `device_*.xml` | UI 层级证据（本地保留，不提交） |
| `device_step.png` | 步骤卡截图（本地保留，不提交） |

未包含：API Key、`.env`、个人媒体、运行数据。真实模型调用与测试替身分开记录。