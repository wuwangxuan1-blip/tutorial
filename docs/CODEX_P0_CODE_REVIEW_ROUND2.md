# P0第二轮代码审查

复查时间：2026-11-05 00:00（Asia/Shanghai）。审查期间码道仍在修改文件；以下基于最后一次检查与构建结果，不把中间版本的编译错误列为现存缺陷。应用代码仍为本地未提交实现，Git基线仍是ab6996a。

## 仍需修复：[P2] 成功任务后的计划获取失败无法正常恢复

位置：`android/app/src/main/java/com/tutorialcoach/app/ui/screens/plan/PlanViewModel.kt:84–86`，以及 `data/SessionRepository.kt:46–50`。

触发步骤：

1. 首次生成计划，服务器Job成功，当前计划版本变为1。
2. 客户端进入succeeded分支，先清空planIdempotencyKey，再调用loadPlan。
3. 如果此时GET计划因网络断开失败，客户端仍没有计划，repository.session.currentPlanVersion仍是null。
4. 恢复网络点击重试：generate生成新幂等键，提交新的plan-jobs请求且base_plan_version=null。
5. 服务端已有版本1，返回409 VERSION_CONFLICT。dismissError只返回Idle，不重新获取已成功的计划；客户端也没有刷新会话的路径。用户无法在原任务中正常恢复。

建议保留成功Job/待取计划状态，在获取计划失败时重试GET而不是再次创建生成任务；获取成功后同步本地会话计划版本。不要简单自动重生成，因为这会丢失已成功结果并增加模型调用。

验收：用测试替身模拟Job成功、首次GET计划网络失败、第二次GET成功；断网恢复后应显示原计划，只有一个计划生成请求，无额外模型调用，无409。另覆盖切换会话后旧结果不覆盖新会话。

证据性质：静态状态与控制流核对，另由独立审查者交叉确认；尚未真机复现。

## 上轮五项复查

| 上轮项 | 本轮结论 | 证据 |
|---|---|---|
| ApiClient缺return | 已修复 | 最新源码使用return response.use；完整安卓构建通过 |
| 计划Job幂等 | 已修复原问题 | 相同key/body在运行中和完成后重放同一个202响应；测试模型只调用一次；不同body返回409 |
| 数组条件文本回答 | 已修复 | normalize_condition_value将文本归一化为数组；烹饪/咖啡ASGI反例已转为200 |
| async修复没有await | 已修复 | 首轮非法、次轮合法的模型替身测试成功，两次调用；新增修复回归测试 |
| 跨会话显示旧计划 | 代码路径已修正 | PlanScreen按session设key；ViewModel观察会话切换、取消旧轮询；Repository拦截旧会话计划写入。尚无设备UI验证 |

上述后端反例使用隔离临时目录、ASGI与模型替身，未使用真实付费模型；源码起止哈希一致后才记录结论。真实模型探针只读取码道已有证据，不代表本轮重新进行付费调用。

## 实际运行的验证

- `server/.venv/Scripts/python.exe -m pytest -q`：21项全部通过。
- 在android目录，以会话级JBR21执行 `gradlew.bat :app:testDebugUnitTest :app:assembleDebug --console=plain`：`BUILD SUCCESSFUL in 27s`。
- APK已生成：`android/app/build/outputs/apk/debug/app-debug.apk`，本次约10.4MB。
- 最初离线测试缺JUnit与coroutines-test缓存；联网解析后测试与构建成功。码道报告中“所有Gradle路径受沙箱拦截”的说法不适用于本次Codex验证环境，应更新报告并保存构建证据。
- 未验证真机安装、实际界面操作、切换会话及断网恢复；不得将构建成功当成设备验收完成。
- 未修改应用源码、未替码道提交或推送。构建与测试产生正常忽略的产物；审查报告是本轮新增文档。

## 交给码道的下一条任务

请读取 docs/CODEX_P0_CODE_REVIEW_ROUND2.md，只修复“成功Job后GET计划失败”的恢复逻辑，补充回归测试；不自动进入P1。获取计划失败后应重试GET原计划，不能新建生成Job或增加模型调用，并同步会话版本。重新运行服务端测试、安卓单元测试和assembleDebug，保存真实证据，更新ENVIRONMENT/IMPLEMENTATION_STATUS中的过期阻塞描述，准确保留未做的真机验收。完成后暂停等待复审。
