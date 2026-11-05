# codearts_proof/day3 索引（P2/D3）

| 文件 | 内容 |
|---|---|
| `README.md` | 本索引 |
| `device_verification.md` | 真机软件主线、步骤/计时/暂停/恢复、提问、条件修改、修订应用/拒绝、杀进程恢复记录 |
| `review_fix.md` | D3 复审三项修复（修订候选计划校验、合并 PATCH、重置计时刷新协程）与回归结果 |
| `review_fix_round2.md` | D3 复审第二轮两项修复（remove 后引用校验、挂起 finished PATCH 与重置竞态）与回归结果 |
| `server_pytest_summary.txt` | 服务端 76 项测试结果摘要（D3 新增 23 + 复审回归 5） |
| `android_test_results.txt` | 安卓 34 项 JVM 测试分套件结果 |
| `android_apk_info.txt` | APK 路径、大小、包名、SDK 版本 |
| `api_checks.md` | PLAN_LOCKED、修订保留已完成步骤、条件 PATCH 语义的服务端检查 |
| `commands.md` | 本轮实际运行命令与关键输出 |
| `handoff_status.md` | 复审修复轮交接状态 |
| `secret_scan.json` | 提交前密钥扫描（226 文件、0 匹配、clean） |
| `git_status.txt` | 提交 `3dc5388` 与推送成功记录（a486b65..3dc5388） |

真实 DeepSeek 调用与测试替身严格区分：本轮真机计划、提问、修订均使用真实服务端 + 真实 DeepSeek；P2/P3 轮的限流与 10 条假设替身结果仍记录在 `codearts_proof/day2/`，不混用。