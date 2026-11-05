# codearts_proof/day4 索引（D4 媒体与反馈）

| 文件 | 内容 |
|---|---|
| `README.md` | 本索引 |
| `vision_probe.json` | 真实文本/JSON/视觉探针；视觉返回“橙色” |
| `plan_photography_real.json` | 真实模型摄影计划（5 步，visual_aid=null） |
| `session_photography.json` | 该摄影会话元数据 |
| `technical_synthetic_feedback.json` | 真实视觉 + 合成图片/合成短片的技术反馈（非真实拍摄） |
| `server_pytest_summary.txt` | 服务端 88 项测试结果摘要 |
| `android_test_results.txt` | Android 41 项 JVM 测试分套件结果 |
| `android_apk_info.txt` | APK 路径、大小、包名、SDK 版本 |
| `media_and_motion.md` | 媒体限制、抽帧时间戳、运动指标方法与失败兜底 |
| `real_material_blocked.md` | 真实图片/短片反馈 BLOCKED 的原因与所需材料 |
| `commands.md` | 实际命令与关键输出 |
| `secret_scan.json` | 提交前密钥扫描 |
| `git_status.txt` | D4 提交与推送记录 |

真实素材与合成素材严格区分：合成图片/视频只用于技术验证，不作为“真实拍摄”演示；真实视觉能力已由探针与合成技术反馈验证，但真实用户素材缺失，真实反馈闸门仍为 BLOCKED。