# P0 代码审查：需修复后复审

审查日期：2026-11-04，约23:24（Asia/Shanghai）。基线提交 `ab6996a`；应用实现目前仍为本地未提交文件。此报告审查当前实现，不把后续阶段未实现的媒体、计时、运镜等功能列为P0缺陷。未修改应用源码、未提交或推送。

## 结论

暂不能通过P0。已建立安卓/服务端分层、类型化DTO、模型错误处理、Job与JSON存储等基础；现有服务端14项测试通过。但安卓存在实际编译错误，且澄清、幂等与模型修复等路径有未被现有测试覆盖的缺陷。

## 1. [P1] 网络客户端缺少返回语句，安卓无法编译

- 位置：`android/app/src/main/java/com/tutorialcoach/app/data/ApiClient.kt:137–161`。
- `execute(...): T` 是块函数，调用 `response.use { ... }` 后未把其结果返回。所有网络调用都依赖此方法，无法生成APK。
- 实际编译输出：`ApiClient.kt:161:5 Missing return statement.`，`:app:compileDebugKotlin FAILED`。
- 修复方向：显式返回 `response.use` 的解析结果，保持响应关闭和错误映射行为；随后重新执行安卓编译与单元测试。

## 2. [P1] 计划任务创建忽略幂等键，重试会重复调用模型

- 位置：`server/app/api/sessions.py:231–275`，尤其第275行。
- 当前只在创建Session时处理 `Idempotency-Key`；创建plan-jobs时未读取或存储此键，每次都创建独立Job。
- 隔离复现：让测试模型等待，对同一会话连续发送相同body和相同幂等键，返回两个不同Job，模型被调用两次；第一个提交成功，第二个最终版本冲突。第一任务已完成后重放则得到409，而不是第一次202的Job。
- 影响：网络重试会重复付费调用，并给用户制造失败任务。违反API契约6.1。
- 修复方向：在创建Job前按method/path/key加锁并校验请求哈希，保存并重放首次响应；同键不同body冲突；覆盖并发重试与首次成功后重放。安卓对同一逻辑重试也应复用原幂等键，而不是每次生成新UUID。

## 3. [P2] 数组条件被声明为文本问题，正常回答会返回422

- 位置：`server/app/services/questions.py:116–129`；答案落入条件模型的位置为 `server/app/api/sessions.py:201`。
- allergies、available_equipment声明为text，validate_answer返回字符串，但Conditions要求字符串数组。taste_preference也有同类问题。
- 隔离复现：创建烹饪会话，提供skill_level/time_budget_min/people/servings但不提供stove_type；收到stove/oven/allergies/equipment问题。按界面填写 `q_stove_type="gas"`、`q_allergies="无"` 后返回422。直接传数组也不符合text问题的答案校验。
- 影响：用户填写过敏或器具信息时无法继续；默认空条件路径也可通过第一轮只提交部分必填项触发该问题。
- 修复方向：统一Question.kind、Android输入组件、Answer序列化与Conditions字段类型。若从自由文本拆分数组，应明确分隔及“无”的语义，避免将未知或过敏信息错误归一化。补完整澄清端到端测试。

## 4. [P2] 模型格式修复请求没有await，重试实际上不执行

- 位置：`server/app/services/plan_service.py:43–66`，尤其61–66行。
- 同步 `_validate_or_repair` 调用异步 `chat_json()` 后直接把协程对象交给Pydantic。不会发起第二次模型请求，却向用户报告“已重试一次仍失败”。
- 隔离复现：首轮返回非法draft，预设第二轮返回合法draft；结果仍为MODEL_BAD_OUTPUT，模型调用次数为1，并出现未await协程警告。
- 修复方向：将验证修复路径改为async并逐层await，保留一次修复与Job总超时预算。补“首次非法、修复成功”“两次非法”“修复超时”测试。
- 阶段说明：完整一次修复属于P1中明确的验收要求，但当前已经实现了这一分支且行为错误；不应带着虚假的重试提示进入下一阶段。

## 5. [P2] 新建第二次练习可能继续显示上一份计划

- 位置：`android/app/src/main/java/com/tutorialcoach/app/ui/screens/plan/PlanViewModel.kt:30–32`；`PlanScreen.kt:41–45`。
- AppRoot手动切换页面；PlanScreen的viewModel没有按session设置key或独立导航作用域。PlanViewModel只在初始化时读取repository.plan，之后保留自己的Ready状态。SessionRepository.createSession虽然清空repository.plan，却不更新这个已有的uiState。
- 触发流程：完成A目标生成→返回首页→新建B目标→进入计划页。Activity作用域中的旧PlanViewModel仍可显示A计划，且Ready状态没有生成按钮，用户无法正常为B生成计划。
- 修复方向：按会话限定ViewModel生命周期/key，或观察Session ID变化重置uiState；取消旧轮询并确保旧Job不能覆盖新会话的计划。补连续创建两次练习的状态/界面测试。
- 证据性质：静态状态流与生命周期分析；尚无真机运行验证。

## 本轮验证结果与边界

1. 在server目录运行 `.venv/Scripts/python.exe -m pytest -q`：14项通过。
2. 使用本机Gradle8.9及会话级JBR21运行 `:app:compileDebugKotlin :app:testDebugUnitTest --console=plain`：依赖解析后进入源码编译，并在ApiClient缺return处失败；安卓测试未运行成功。
3. 离线构建先因Kotlin serialization插件未缓存失败；随后正常解析依赖进入源码编译。不能把离线缓存缺失当成代码编译结论。
4. 后端反例用隔离ASGI应用和测试模型复现，没有调用收费模型，没有改真实会话数据。审查临时数据在项目 `work/backend-review-slow-job/`，不是应用交付物，勿加入提交。
5. 未执行本次真实文本/图片/JSON探针，未验证真机安装；检查时 `scripts/probe_deepseek.py`、`server/requirements.txt` 尚不存在，P0报告/证据仍多处标待运行。代码目录也尚未提交。以上必须在最终P0报告中准确列明，不得用14项单元测试代替完整验收。

## 可复制给码道的修复任务

请完整读取 docs/CODEX_P0_CODE_REVIEW.md，只修复审查项1–5及其必要回归测试，不自动进入P1，不削减产品范围。代码位置以当前文件为准；如文件已变化，逐项说明是否仍适用和验证证据。

先修复安卓编译错误，再修复plan-jobs幂等与澄清数组类型，接着修复async重试与跨会话UI状态。每项补能暴露原缺陷的测试，验证后更新docs/IMPLEMENTATION_STATUS.md。补齐P0原定探针/依赖锁文件与真实证据；缺设备或模型能力仍准确标BLOCKED，不伪造。最后运行服务端测试、安卓testDebugUnitTest和assembleDebug，报告实际结果、APK路径、剩余阻塞与Git状态，暂停等待复审。不把审查临时work目录、密钥或个人媒体提交。
