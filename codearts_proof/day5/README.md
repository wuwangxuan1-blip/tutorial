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
| `review_fix_round6.md` | D5 复审收尾：总水量 vs 闷蒸注水、总时长优先与中文分钟步骤改写 |
| `review_fix_round7.md` | D5 配方解析优先级：显式总水量优先于阶段注水、无总量仅唯一终值、中英文冒号总时长、调整只改总时长 |
| `review_fix_round8.md` | D5 创建/调整总量一致性：共用来源识别、`注水总量` 按位置改写、静置/闷蒸单步时长不改 |
| `review_fix_round9.md` | D5 调整总量来源定位：整份配方只定位一次、`注水 225 g` 可调整、跨步骤总时长/单步用时分离、无法定位 422 |
| `review_fix_round10.md` | D5 创建期来源固化：创建前校验可调整来源、总量与最终停止条件同步、中途注水不变、仅摘要来源 422 |
| `review_fix_round11.md` | D5 总水量下限校验：新总量低于中途累计注水目标 422 不落库、240 g 成功且中途 100 g 不变 |
| `review_fix_round12.md` | D5 连续调整目标身份保留：225→100→240 时中途 100 g 不变、最终 240 g；90 g 仍 422 |
| `review_fix_round13.md` | D5 总量来源身份持久化：`Recipe.total_sources` 跨版本复用、`继续注水至` 不作最终判据、无 marks 422 |
| `review_fix_round14.md` | D5 最后执行指令身份与旧配方恢复：结构判据同步最后注水指令、旧配方自动补 marks、同值歧义 422 + confirmation |
| `review_fix_round15.md` | D5 总量冲突检测与 Android 确认流程：显式总量 vs 最终停止条件冲突 422；确认弹窗/取消/版本冲突 |
| `server_pytest_summary.txt` | 后端 136 passed 测试摘要 |
| `android_test_results.txt` | Android 58 tests / 0 failures 分套件结果（含 easing 与 seek 回归） |
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
- D5 配方复审收尾已提交 `bd1fe0c`（证据 `f32f4e6`，状态记录 `0e254a2`）并成功推送 `1376a51..0e254a2`，远端 `main = 0e254a2`；密钥扫描 298 文件 0 匹配 clean；推送后复跑后端 116 passed、Android 55 tests、APK 10,822,322 字节。详见 `git_status.txt`。
- D5 配方解析优先级修复（基线 `0e254a2`）：显式总水量优先于阶段注水（闷蒸 30→100→150 + 总水量 225 = 225 g）；无显式总量时仅接受唯一累计终值，多阶段/仅闷蒸局部量 422；总时长支持中英文冒号并优先于单步用时，调整只改总时长。服务端 120 passed、Android 55 tests、APK 10,822,322 字节；状态分列不变。详见 `review_fix_round7.md`、`git_status.txt`。
- D5 配方创建/调整总量一致性（基线 `991b4b6`）：创建与调整共用来源识别；`注水总量：225 g` 改 240 g 后参数、用料、步骤一致，阶段注水与闷蒸量不变；`总时长：150 秒，静置时长 150 秒` 改 180 只改总时长。服务端 122 passed、Android 55 tests、APK 10,822,322 字节。详见 `review_fix_round8.md`。
- D5 配方调整总量来源定位（基线 `ac538ef`）：整份配方只定位一次来源；`注水 225 g` 改 240 g 后参数、用料、步骤一致；步骤 0 `总时长：150 秒` 与步骤 1 `萃取用时 150 秒` 改 180 时只更新总时长；无法定位来源返回 422 `total_source_unconfirmed`。服务端 125 passed、Android 55 tests、APK 10,822,322 字节。详见 `review_fix_round9.md`。
- D5 创建期来源固化（基线 `b7e923c`）：创建前校验总水量/总时长可在步骤中定位，仅摘要来源直接 422 提示确认；总水量 225 g 与“继续注水至 225 g 后停止”同步改 240 g，中途 100 g 不变；旧版保留原值。服务端 127 passed、Android 55 tests、APK 10,822,322 字节。详见 `review_fix_round10.md`。
- D5 总水量下限校验（基线 `f840d03`）：中途 `注水至 100 g`、最终 `继续注水至 225 g 后停止` 时，总量改 90 g 返回 422 `intermediate_water_exceeds_total` 且旧版/历史不变；改 240 g 成功，中途仍 100 g、最终 240 g。服务端 128 passed、Android 55 tests、APK 10,822,322 字节。详见 `review_fix_round11.md`。
- D5 连续调整目标身份保留（基线 `43b6e23`）：先 225→100 再 100→240 时，最新版中途仍 100 g、最终停止条件与用料为 240 g，v1/v2 历史按原值回查；90 g 仍 422 不写入。服务端 129 passed、Android 55 tests、APK 10,822,322 字节。详见 `review_fix_round12.md`。
- D5 总量来源身份持久化（基线 `a90c82a`）：`Recipe.total_sources` 跨版本记录总量声明/最终停止条件，`继续注水至` 不再单独作为最终判据；225→100→240 时中途 100 g、等待 10 秒不变，最终 240 g；无 marks 旧配方 422。服务端 131 passed、Android 55 tests、APK 10,822,322 字节。详见 `review_fix_round13.md`。
- D5 最后执行指令身份与旧配方恢复（基线 `ad81680`）：`总水量 225 g` + `分两次注水至 225 g，等滤杯滴完` 改 240 g 后参数、用料与最后指令一致；旧配方首次调整自动补齐 marks，同值歧义 422 并可用 `water_source_confirmation` 确认后成功，历史原值保留。服务端 134 passed、Android 55 tests、APK 10,822,322 字节。详见 `review_fix_round14.md`。- D5 总量冲突检测与 Android 确认流程（基线 `3c86b6e`）：`总水量 225 g，最后注水至 220 g 后停止` 创建/调整返回 422 `water_total_conflicts_with_final` 且不写入；Android 收到 `confirmation_required` 展示候选并确认/取消/版本冲突重试。服务端 136 passed、Android 58 tests、APK 10,838,706 字节。详见 `review_fix_round15.md`。