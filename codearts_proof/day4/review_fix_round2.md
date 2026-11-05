# D4 复审修复（第二轮，2026-11-05）

基线：`ba1eb52`（D4 代码/测试/证据提交 `d532ce0`）。本轮只修复 Codex 复审的两项问题，不进入 D5。

## 1. 反馈分析完成后的会话写入不再覆盖最新状态

**问题**：反馈任务在模型调用期间不持会话锁，但分析结束写回证据等级时直接使用任务开始时加载的 session 快照；若期间保存了进度/计时或应用了修订，旧快照会覆盖最新状态。

**修复**（`server/app/services/feedback_service.py`）：

- 新增 `_persist_feedback()`：在 `store.lock(session_rel(session_id))` 内重新加载最新会话。
- 核对会话状态、`current_plan_version` 与本次反馈的 `plan_version`、`step_id` 是否仍在当前计划。
- 版本变化返回 `409 VERSION_CONFLICT`（带 `current_plan_version`），不写 Feedback。
- 只合并 `progress.evidence_levels[step_id]`（`measured` 保持，否则 `model_observed`）；`current_step_id`、`step_statuses`、`timer` 等其他字段保留最新值。
- 模型调用期间不持有会话锁。

**回归**（`server/tests/test_feedback.py`）：

- `test_feedback_analysis_keeps_progress_saved_while_model_runs`：可挂起 fake 模型分析期间 PATCH 当前步骤、步骤状态与运行中计时；释放后 Job 成功，最新进度/计时保留，仅证据等级变为 `model_observed`。
- `test_feedback_analysis_does_not_write_after_revision_changes_plan`：分析期间生成并应用修订使计划升至 v2；释放后反馈 Job 失败 `409 VERSION_CONFLICT`，Feedback 不落盘，会话保持 v2，证据等级未被旧快照写回。

## 2. 视频证据缩略图按实际 frame_index/timestamp_s 提取

**问题**：反馈页对所有视频帧观察都复用视频开头缩略图，未对应观察实际引用的帧/时间戳。

**修复**：

- `MediaLoader` 新增 `extractEvidenceFrame(videoFile, timestampS)`；`MediaPreparer` 用 `MediaMetadataRetriever.getFrameAtTime(timestamp*1e6, OPTION_CLOSEST)` 提取并压缩为 JPEG，失败返回 null。
- `MediaViewModel` 收到反馈后为每个 `video_frame` 观察按 `mediaId|frameIndex|timestampS` 生成证据帧映射；取不到不加入。
- `MediaScreen.EvidenceThumbnail` 视频帧只查该映射；缺失显示“证据帧不可用”，不再回退视频开头 `thumbnail`。

**回归**（`MediaViewModelTest`，JVM）：

- `videoEvidenceFramesFollowEachObservationTimestamp`：同一视频两个观察（0s/frame 0、2s/frame 2）分别请求 0.0/2.0 并得到不同文件；不存在的 1s 返回 null。
- `missingEvidenceFrameIsUnavailableWithoutVideoThumbnailFallback`：提取失败时证据帧为空，即使视频开头缩略图存在也不用于证据。

## 本轮实测

- 服务端：`.venv/Scripts/python.exe -m pytest -o addopts=""` → **90 passed / 0 failed**（较 D4 基线 88 增加 2 项）。
- Android：`:app:testDebugUnitTest --rerun-tasks` → **43 tests / 0 failures**（`MediaViewModelTest` 4 项）。
- `:app:assembleDebug` → BUILD SUCCESSFUL；APK `android/app/build/outputs/apk/debug/app-debug.apk`，10,798,800 字节。
- `git diff --check` 通过；密钥扫描 262 文件、0 匹配、clean。

## 真实素材状态

- 真机技术走查曾选择设备相册中的界面截图并经 Photo Picker 上传，真实视觉反馈明确识别为“烹饪计划步骤卡截图”，不是咖啡拍摄照片。
- 因此**真实拍摄图片/真实短片反馈仍为 BLOCKED**；没有用截图或合成素材冒充真实拍摄验收。

## 范围

- 未实现 Canvas 运镜、咖啡配方或 D5 任何能力；等待 D4 复审结论。