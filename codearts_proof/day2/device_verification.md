# D2 真机复测（2026-11-05）

## 环境

- 设备：realme GT6 / RMX3800，Android 16，1264×2780，adb `eeffd16b device`
- APK：当前源码构建，`adb install -r` Success
- 服务端：FastAPI `127.0.0.1:8000`，`adb reverse tcp:8000 tcp:8000`
- 首页显示“服务端：正常”

## 烹饪完整文本流程

1. 首页输入 `two servings tomato egg noodles in 30 minutes`（adb 自动化只能注入 ASCII；中文目标在服务端真实流程中验证）。
2. 首轮 5 个关键问题：只回答熟练度、时长，提交后进入**第二轮**（3 个问题：人数/份量/灶具）。
3. 第二轮回答 3 个必填项；可选问题留空跳过；会话进入 `ready`。
4. 点击“生成计划（真实模型）”：真实模型调用 **27.079 s / 4682 tokens**。
5. 计划页显示：
   - 标题“30分钟两人份番茄鸡蛋面”
   - 预计 30 分钟、版本 v1、5 步
   - **假设** 6 条（3 条模型假设 + 3 条服务端对未提供过敏/器具/烤箱的假设）
   - 准备清单 3 条
   - 安全提示
6. 打开步骤卡：第 1/5 步；点击“下一步”到第 2/5 步；每步显示可观察完成标准与安全提示。
7. logcat 未发现 FATAL/AndroidRuntime 崩溃。

## 界面文本证据

`device_home.xml`、`device_clarify1.xml`、`device_clarify2.xml`、`device_plan_with_assumptions.xml`、`device_plan_bottom.xml`、`device_step.xml`、`device_step2.xml`。

截图 `device_step.png` 仅在本地，不提交。

## 未覆盖

- 旋转、切后台、进程被杀恢复；
- 中文输入法直接输入目标（本次设备端使用 ASCII 目标；服务端真实流程使用中文目标）；
- 视觉检查截图（本模型不支持图片输入，结论来自 UI 层级文本与服务端日志）；
- 计时/媒体/运镜/配方/参考教程属于后续阶段。