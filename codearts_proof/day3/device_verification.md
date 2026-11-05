# P2/D3 真机验证（2026-11-05）

## 环境

- 设备：realme GT6 / RMX3800 / Android 16（SDK 36），1264×2780，adb `eeffd16b device`，设备代号 `RE5C4FL1`。
- APK：当前源码构建，`adb install -r` → `Success`；包名 `com.tutorialcoach.app`，versionName 0.1.0，minSdk 26 / targetSdk 35。
- 服务端：真实 FastAPI `127.0.0.1:8000`，使用本地 `server/.env` 的 DeepSeek 配置；`adb reverse tcp:8000 tcp:8000`；首页显示“服务端：正常”。
- 模型：本轮真机计划生成、步骤提问、条件修订均调用真实 DeepSeek（不是测试替身）。

## 1. 软件主线（真实模型）

会话：`sess_01M6NG28XPBB3SFPE71DM6ZJDQ`。

1. 首页输入 `copy photos to a new folder and rename by date in Windows 11`，选择“软件与数字技能”，创建会话。
2. 澄清页回答熟练度“初学者”、操作系统“Windows”，并回答备份“是”；会话进入 `ready`。
3. 计划页点击“生成计划（真实模型）”，真实模型返回：
   - 标题：“Windows 11 照片复制到新文件夹并按日期重命名”
   - 5 步、版本 v1、预计 27 分钟
   - 假设包含“未提供系统版本，按主流 Windows 11 版本假设”“未提供终端可用性，按图形界面操作为主假设”
   - 准备清单含备份、目标文件夹确认、详细信息视图、命名格式
   - 安全提示含“任何复制或重命名前先确认备份可用”“命令和快捷键只作为教学文本，不会自动执行”
4. 步骤 1 为“备份源照片并确认可读”，完成标准为“备份文件夹中的照片数量与所选源照片一致”“随机打开至少 3 张备份照片可正常显示”“源照片仍保留在原文件夹”。

## 2. 步骤与进度（真机）

1. 步骤卡显示第 1/5 步，状态“未开始 · 证据：未提供”。
2. 点击“下一步” → 第 2/5 步，状态“进行中”。
3. 点击“上一步” → 第 1/5 步，状态“进行中”。
4. 点击“开始计时” → “计时中 · 4:56 / 5:00”。
5. 点击“暂停计时” → 状态“已暂停”，按钮变为“继续计时”。
6. 点击“继续计时” → “计时中 · 4:43 / 5:00”，剩余时间连续，无负值。
7. 点击“完成本步” → 自动进入第 2/5 步，提示“已标记完成（self_reported）”。
8. 服务端核对：

```json
{"current_step_id":"step_2","step_statuses":{"step_2":"in_progress","step_1":"done"},"evidence_levels":{"step_1":"self_reported"},"timer":null}
```

用户点完成只写 `self_reported`，未自动写入 `model_observed`；下一步不改变验证状态。

## 3. 提问（真实模型）

- 在第 2 步输入问题 `how to verify the copy is correct`，点击“发送问题”。
- 真实模型返回可操作回答：先对比源/目标文件数，再按名称、大小、修改日期抽查，随机打开照片确认可显示；并明确“不要仅凭数量认定内容完全一致”。

## 4. 暂停/恢复与暂停写入拒绝

1. 点击“暂停练习” → 会话 `paused`，页面提示“练习已暂停；暂停期间不能写入进度”。
2. 在暂停状态点击“保存进度” → 页面显示错误：“会话已暂停，不能写入进度；请先恢复。”（HTTP 409 `SESSION_PAUSED`）。
3. 点击“恢复练习” → 会话 `in_progress`，提示“练习已恢复”。

## 5. 条件修改与修订（真实模型）

1. 进入“修改条件”，修改备注为 `add a verification step after copy`，提交。
2. 返回 impact：“已有步骤进度，不能全量重新生成。请用条件修订调整未完成步骤，或新建会话。”、`changed_fields=["notes"]`、`requires_revision=true`。
3. 进入“修订提案”，输入原因 `adjust unfinished steps to add a verification check after copy`，生成修订。
4. 真实模型返回 `proposed` 修订，变更 `step_2`、`step_3`、`step_4`（未触碰 `done` 的 `step_1`），每条包含 before/after/reason。
5. 点击“应用”：
   - 页面提示“修订已应用；计划版本 +1，已完成/跳过步骤保持不变。”
   - 服务端会话 `current_plan_version=2`，进度仍为 `step_1=done` + `self_reported`、`step_2=in_progress`。
   - 服务端对比 v1/v2：`step_1` 内容完全一致（`v1 step1 == v2 step1: True`）。
6. 再次生成一个修订（`proposed`，基于 v2），点击“拒绝”；服务端列表显示该修订 `rejected`。

## 6. 杀进程恢复

1. 在第 2 步启动计时后 `adb shell am force-stop com.tutorialcoach.app`。
2. 重新启动 App：自动恢复上次会话，计划页显示计划版本 **v2**、5 步。
3. 打开步骤卡：第 2/5 步、状态“进行中”；计时器显示“计时中 · 4:10 / 5:00”，说明服务端进度与计时锚点恢复成功。

## 7. 服务端 API 检查（同一会话）

- 有进度时 `POST /v1/sessions/{id}/plan-jobs`（`base_plan_version=2`）→ **409 `PLAN_LOCKED`**。
- 修订应用保持 `done` 步骤内容与证据不变（见第 5 节）。
- 条件 PATCH、空字符串、关键字段 null 的细分语义由 `server/tests/test_conditions.py` 覆盖。

## 8. 真实模型与未验证边界

已用真实 DeepSeek：

- 软件计划（5 步，v1）。
- 步骤提问（第 2 步回答）。
- 条件修订生成（两次；一次应用、一次拒绝）。

未验证 / 不得当作已通过：

- 设备重启后的计时确认弹窗（本轮未重启设备；JVM `TimerEngineTest` 覆盖锚点失效判定）。
- 旋转恢复（尝试修改设备旋转设置时被权限拒绝，未执行；后续需用户授权或手工旋转复测）。
- 中文输入法直接输入目标（设备端自动化仅注入 ASCII）。
- 截图 AI 视觉检查（结论来自 UI 层级文本、服务端会话/计划/修订 JSON 与日志）。
- 真实 DeepSeek 恰好触发 429 与一次返回 10 条假设（仍由 P2/P3 轮的测试模型替身覆盖，记录在 `day2`）。
- 媒体反馈、运镜、配方、参考教程属 D4+，本轮未实现。

## 9. 服务端真实烹饪回归（非设备 UI）

使用真实服务端 + 真实 DeepSeek 创建烹饪会话 `sess_01M6NJ7TMDHPXR5GRWPV8CCGP7`（2 人份番茄鸡蛋面，30 分钟）：

- 计划 5 步，标题“2人份番茄鸡蛋面（30分钟内）”。
- 假设包含“未提供过敏信息，请核对本次实际使用的食材和调味料；无法确认是否存在过敏原。”
- 未出现番茄/鸡蛋/面条被写入通用过敏提示的固定菜谱描述。

该流程通过服务端 API 执行，不是设备端烹饪 UI 复跑；设备端本轮主线为软件领域。