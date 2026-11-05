# D4 媒体、抽帧与运动指标

## 媒体限制（服务端实测）

- 图片：JPEG/PNG/WebP；≤10 MiB；1–4 张；服务端转 RGB JPEG、去 EXIF、长边 1024；HEIC/HEIF 服务端返回 415，由 App 先转 JPEG。
- 视频：MP4/MOV；≤30 秒、≤100 MiB；每次反馈恰好 1 段；ffprobe 10s 超时，首帧解码失败 → `MEDIA_DECODE_FAILED`。
- 数量/混用：图片 1–4；视频 1；图片与视频不能混用；重复 media_id/未知媒体拒绝。

## 抽帧

- 1 fps，最多 8 帧；示例 8 秒视频实际时间戳 `[0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]`。
- 长边 1024 JPEG；反馈证据必须引用本次 media_id；视频证据必须 frame_index 与实际帧一致、timestamp_s 误差 ≤0.02。

## 运动指标

- 方法：`fps=10, scale=320:-2, format=gray, vidstabdetect(fileformat=ascii)`，再用 `vidstabtransform(debug=1)` 读取 `global_motions.trf`。
- 输出：`method=vidstabdetect_ascii_10fps_320px+global_motions`、sample_fps=10、frame_count、mean/p95 translation、mean rotation、direction_changes、4 条固定局限。
- 合成 8 秒视频实测：frame_count=80，mean_translation_px=0.043，p95=0.129，mean_rotation_deg=0.003。
- vidstabdetect/vidstabtransform 失败或输出不可解析 → `motion_metrics=null`，追加“未启用运动估计（vidstabdetect 失败或不可用）。”，不填零、不编造。
- 不使用 OpenCV；不分析音频；`audio_analyzed=false`。

## 反馈证据与安全边界

- 每条 observation 必须引用本次媒体；图片 frame 字段必须为 null；视频 frame 与 timestamp 必须来自实际抽帧。
- assessment 仅 not_verified/likely_met/unclear/not_met；证据不足用 unclear/not_verified。
- 图片不推断内部温度/食用安全/口味；短片不编造 0–100 稳定性评分。
- 反馈不自动修改步骤状态；无观察时不标 `model_observed`。
- 合成素材真实视觉实测：图片与短片均 `not_verified`，模型明确指出合成素材、测试卡，不替代现场验证。