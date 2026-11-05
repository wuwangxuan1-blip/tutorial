# codearts_proof/day5 索引（D5 摄影运镜与咖啡配方）

| 文件 | 内容 |
|---|---|
| `README.md` | 本索引 |
| `real_flow.json` | 真实模型摄影计划 + V60 配方版本链/对比摘要（92→90；口味字段为脚本测试输入，不是真实用户品尝） |
| `plan_photography_real.json` | 真实模型摄影计划，含合法 `camera_move`（orbit_cw，8 秒） |
| `plan_coffee_real.json` | 真实模型 V60 计划，含 15 g / 225 g / 92 °C / 150 秒与设备替代提示 |
| `third_party_assets.json` | 两份 Wikimedia 素材的来源、作者、许可、SHA-256、转码/ffprobe 记录 |
| `source/` | 两份素材的 Wikimedia API 元数据副本；原始 HTML 页面保留在 `work/`，SHA-256 见 manifest |
| `third_party/README.md` | 第三方实拍链路实际结果、帧字节一致性、许可边界 |
| `third_party/real_feedback.json` | 照片/短片/倒咖啡反例的真实模型完整输出与证据帧 SHA-256 比对 |
| `third_party/plan_photography_feedback.json` | 该真实反馈会话的 5 步摄影计划 |
| `third_party/photo_input.jpg` | 实际送给模型的压缩照片（CC0 素材派生） |
| `third_party/frames/` | 短片派生的证据帧（CC BY-SA 4.0，署名见 `third_party/README.md`） |
| `review_fix_round4.md` | D5 三项复审修复：按计划参数/demo、派生粉水比与步骤同步、Canvas easing |
| `review_fix_round5.md` | D5 复审再修：语义化步骤更新、中文时长解析、先校验后派生 |
| `server_pytest_summary.txt` | 后端 114 passed 测试摘要 |
| `android_test_results.txt` | Android 55 tests / 0 failures 分套件结果（含 easing 与 seek 回归） |
| `android_apk_info.txt` | APK 路径、大小与构建结果 |
| `device_verification.md` | 真机运镜、咖啡品尝/调整与断网重试记录、BLOCKED 项 |
| `device_camera_playing.png` | 真机运镜播放中的脱敏截图（本轮代码前的同一 D5 运镜页面） |
| `device_camera_paused.png` | 真机运镜暂停/重播后的脱敏截图 |
| `secret_scan.json` | 提交前密钥扫描 |
| `git_status.txt` | D5 提交与推送记录 |

## 结论边界

- **第三方实拍链路：通过**。照片/短片真实反馈均成功；短片主反馈 4/4、反例 5/5 取帧字节与模型输入一致；倒咖啡反例被模型判为 `not_met`。
- **用户自拍环绕验收：BLOCKED**（无用户自拍环绕素材）。
- **合成技术回归：另见 D4**，不与第三方实拍或用户自拍合并。
- 真机咖啡：v1 与用户评分已通过 UI 保存（服务端 201）；92→90 调整与对比未在真机完成，断网重试未触发成功，均标 BLOCKED（工具权限拒绝，未重试/未伪造）。
- D5 配方复审再修已提交 `4e08391`（证据 `f9dddfd`）；密钥扫描 297 文件 0 匹配 clean。推送与最终远端 SHA 以 `git_status.txt` 为准。