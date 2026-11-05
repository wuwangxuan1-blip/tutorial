# D4 真实素材状态：BLOCKED

- 仓库内可见媒体只有 `codearts_proof/day1/device_home.png`、`device_step.png`、`day2/device_step.png` 等界面截图；`work/` 只有 UI XML 与 D3 日志，没有用户真实拍摄的照片或短片。
- 因此“真实图片反馈”和“真实短片反馈”各一次验收均为 **BLOCKED**：缺真实图片、缺真实短片。
- 没有用项目截图冒充真实练习照片，也没有把合成素材写成真实拍摄结果。
- 已完成的替代验证：
  - 真实视觉探针：`vision_probe.json`（文本/JSON/视觉 ok，橙色识别正确）。
  - 真实视觉 + 合成素材技术反馈：`technical_synthetic_feedback.json`（图片与 8 秒合成短片；模型明确指出是合成素材，评估 `not_verified`）。
- 解阻条件：提供 1 张真实拍摄照片（JPEG/PNG/WebP，≤10 MiB）与 1 段真实短片（MP4/MOV，≤30 秒、≤100 MiB），再分别提交反馈并保存脱敏结果。设备端还需真机走查 Photo Picker 与上传/反馈页。
## 2026-11-05 真机技术走查更新（仍 BLOCKED）

- 真机走查使用设备相册中的**界面截图**（来源 `codearts_proof/day1/device_step.png`，本地副本 `work/device_d4/tech_photo.png`）与 8 秒合成 testsrc 短片，仅用于验证 Photo Picker、图片压缩、上传、反馈页与真实视觉链路。
- 真实视觉反馈明确识别截图为“2 人份 30 分钟西红柿鸡蛋面实践计划”的步骤卡页面，并指出“本次没有提交任何咖啡杯取景照片或视频帧”。
- 因此上述走查**不是真实拍摄验收**；真实咖啡照片/真实短片反馈仍为 **BLOCKED**，解阻条件不变。
- 未用截图或合成素材冒充真实拍摄结果。
## 2026-11-05 第三方实拍补验（第三方链路通过，用户自拍仍 BLOCKED）

- 使用 Wikimedia CC0 照片 `Coffee cup seen from above.jpg` 与 CC BY-SA 4.0 短片 `A man pours Arabic coffee.ogv`（Sarah Canbel）通过真实后端/真实视觉模型各跑一次反馈。
- 照片实际输出 `unclear`（主体、构图、可见光线均被描述；无口味/安全推断）；短片主反馈 `unclear`，4/4 证据帧与模型输入逐字节一致；倒咖啡短片提交到“手机环绕拍咖啡 8 秒”步骤 3，模型实际返回 `not_met`，明确指出去咖啡动作而非环绕。
- 因此 **第三方公开授权实拍链路已通过**；但 **用户自拍“环绕咖啡 8 秒”素材仍缺失，用户自拍环绕反馈仍 BLOCKED**。
- 详细来源、许可、SHA-256、处理与输出见 `codearts_proof/day5/third_party_assets.json`、`codearts_proof/day5/third_party/README.md`、`real_feedback.json`。素材未用于微调/批量训练，未冒充用户自拍。