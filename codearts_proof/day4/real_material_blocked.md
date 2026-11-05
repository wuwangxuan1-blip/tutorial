# D4 真实素材状态：BLOCKED

- 仓库内可见媒体只有 `codearts_proof/day1/device_home.png`、`device_step.png`、`day2/device_step.png` 等界面截图；`work/` 只有 UI XML 与 D3 日志，没有用户真实拍摄的照片或短片。
- 因此“真实图片反馈”和“真实短片反馈”各一次验收均为 **BLOCKED**：缺真实图片、缺真实短片。
- 没有用项目截图冒充真实练习照片，也没有把合成素材写成真实拍摄结果。
- 已完成的替代验证：
  - 真实视觉探针：`vision_probe.json`（文本/JSON/视觉 ok，橙色识别正确）。
  - 真实视觉 + 合成素材技术反馈：`technical_synthetic_feedback.json`（图片与 8 秒合成短片；模型明确指出是合成素材，评估 `not_verified`）。
- 解阻条件：提供 1 张真实拍摄照片（JPEG/PNG/WebP，≤10 MiB）与 1 段真实短片（MP4/MOV，≤30 秒、≤100 MiB），再分别提交反馈并保存脱敏结果。设备端还需真机走查 Photo Picker 与上传/反馈页。