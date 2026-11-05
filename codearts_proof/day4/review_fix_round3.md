# D4 复审修复（第三轮，2026-11-05）

基线：`40676b1`。本轮只修 D4 剩余 P2，不进入 D5。

## 问题

Android 用 `MediaMetadataRetriever.OPTION_CLOSEST` 按 `timestamp_s` 重新解码视频取缩略图；重新解码不保证与模型实际看到的抽帧是同一份图像，仍可能张冠李戴。

## 修复

**服务端保留模型输入帧**

- `FeedbackService.analyze` 在视频抽帧后，把实际送入模型的每个 `frame_index` 对应 JPEG 字节保存在内存，反馈写入时持久化到 `server/data/feedback_frames/{feedback_id}/frame_{frame_index}.jpg`。
- 保存发生在会话锁内、计划版本/步骤校验之后、Feedback 落盘之前；版本冲突时不写 Feedback。
- 新增 `GET /v1/feedback/{feedback_id}/evidence-frames/{media_id}/{frame_index}?timestamp_s=...`：
  - 只返回反馈 observations 中实际引用、且 `media_id/frame_index/timestamp_s` 匹配（误差 ≤0.02）的帧；
  - 返回保存的 JPEG 原始字节（即模型输入帧），不重新解码视频；
  - 反馈不存在、媒体不属于该反馈、帧/时间戳不匹配、帧文件缺失 → 404 `NOT_FOUND`。
- 契约补充：`docs/API_CONTRACT.md` 3.7 与 4.4。

**Android 直接显示服务端帧**

- 移除 `MediaLoader.extractEvidenceFrame`（不再本地重新解码视频）。
- `FeedbackGateway/ApiClient/SessionRepository` 新增 `getEvidenceFrame`，下载服务端保存的帧字节。
- `MediaViewModel` 对每个 `video_frame` 观察按 `mediaId|frameIndex|timestampS` 下载并写入本地缓存；404/网络失败/写入失败一律不加入映射。
- 反馈页视频帧只显示映射中的服务端帧；缺失显示“证据帧不可用”，不回退视频开头缩略图。

## 回归

- 服务端 `test_video_evidence_frames_are_exact_model_input_frames`：同一 2 秒短片的两个观察（frame 0/0.0s、frame 1/1.0s）；测试捕获模型实际收到的 `vision_images` 字节，断言取帧端点返回的字节与对应模型输入帧逐字节相同、两帧不同；错误时间戳与不存在反馈返回 404。
- Android `videoEvidenceFramesUseServerProvidedBytesForEachObservation`：两个观察分别下载两份不同的服务端字节，生成本地缓存文件内容与字节一致；未引用时间戳返回 null。
- Android `missingEvidenceFrameIsUnavailableWithoutVideoThumbnailFallback`：服务端无帧时映射为空，即使视频开头缩略图存在也不用于证据。
- 保留并发与版本冲突回归：`test_feedback_analysis_keeps_progress_saved_while_model_runs`、`test_feedback_analysis_does_not_write_after_revision_changes_plan`（本轮仍通过）。

## 本轮实测

- 服务端：`.venv/Scripts/python.exe -m pytest -o addopts=""` → **91 passed / 0 failed**（D4 上一轮 90 + 证据帧端点 1）。
- Android：`:app:testDebugUnitTest --rerun-tasks` → **43 tests / 0 failures**。
- `:app:assembleDebug` → BUILD SUCCESSFUL；APK 10,816,510 字节。
- `git diff --check` 通过；密钥扫描 263 文件、0 匹配、clean。

## 真实素材

真实拍摄图片/短片反馈仍为 **BLOCKED**；合成短片仅用于技术测试，不构成真实拍摄验收。