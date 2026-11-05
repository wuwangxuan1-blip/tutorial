# 真机验证记录（2026-11-05）

## 设备与服务端

- 设备：realme GT6，型号 `RMX3800`，Android 16，物理分辨率 1264×2780，adb 序列号 `eeffd16b`，状态 `device`。
- APK：`android/app/build/outputs/apk/debug/app-debug.apk`，`adb install -r` 返回 `Success`。
- 服务端：FastAPI/uvicorn 监听 `127.0.0.1:8000`，已执行 `adb reverse tcp:8000 tcp:8000`。
- App 首页显示“服务端：正常”。

## 已完成的真机验收

| 项 | 结果 |
|---|---|
| 安装 APK | PASS（`Success`） |
| 启动 App | PASS（冷启动成功） |
| 首页服务端状态 | PASS（“服务端：正常”） |
| 创建会话 | PASS：目标 `tomato egg noodles for 2 people in 30 minutes`，返回 5 个澄清问题 |
| 澄清并进入 ready | PASS：回答熟练度/时长/人数/份量/灶具后进入计划页 |
| 真实模型计划 | PASS：标题“2人份30分钟西红柿鸡蛋面实践计划”，v1，5 步；服务端真实调用 26.449 s / 4445 tokens |
| 步骤卡 | PASS：显示第 1/5 步；点击“下一步”后显示第 2/5 步 |
| 诊断页 | PASS：`status=ok`、api v1、store/ffmpeg/model_configured 均为 true；文本/图片模型 `deepseek-flash`；`vision_supported=探针通过`；4 领域列表 |
| 跨会话隔离 | PASS：新建 `quick fried rice for 1 person in 15 minutes` 会话后，计划页显示“条件已就绪”，没有上一会话计划残留 |
| 断网提示 | PASS：停止服务端后刷新首页显示“服务端：未连接” |
| 服务恢复 | PASS：重启服务端后刷新显示“服务端：正常” |
| 崩溃检查 | PASS：logcat 未发现 FATAL/AndroidRuntime 崩溃行 |

## 证据（本地，未提交个人媒体）

- UI 树：`codearts_proof/day1/device_home.xml`、`device_clarify.xml`、`device_plan.xml`、`device_plan_after.xml`、`device_plan_bottom.xml`、`device_step.xml`、`device_step2.xml`、`device_diagnostics.xml`、`device_offline.xml`、`device_recovered.xml`。
- 服务端脱敏日志：`codearts_proof/day1/device_server.log`。
- 截图：`device_home.png`、`device_step.png`（只在本地，不提交；截图可能包含设备状态栏）。
- 未提交 `device_*.xml` 与截图，避免个人设备信息进入 Git；本文件为脱敏摘要。

## 尚未验证/已知边界

- 未测试旋转、切后台、进程被杀后的恢复（P0 不要求持久化，D3 再做）。
- 未在设备上输入中文目标；adb `input text` 只输入 ASCII，实际中文键盘输入未验证（不是 App 缺陷）。
- 第二个会话只验证“无旧计划残留”，未再次调用真实模型生成第二份计划。
- 截图未由 AI 视觉检查（本模型不支持图片输入），结论来自 UI 层级文本与服务端日志。
- 计时、完成标记、媒体反馈、运镜、配方、参考教程属于后续阶段，未在 P0 实现。