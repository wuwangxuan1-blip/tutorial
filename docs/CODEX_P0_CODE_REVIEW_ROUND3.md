# P0第三轮代码审查

时间：2026-11-05 00:41（Asia/Shanghai）。审查提交 `f9bb1e055533371fdfe1cc0e8deaa33363195124`。审查前工作区干净；本轮不修改应用源码、测试或Git状态，仅新增本报告。

## 结论

上一轮“成功Job后GET计划失败无法恢复”的实现已修正：保留待获取计划会话、重试GET而非新建Job、读取成功后同步计划版本。当前应用可构建APK，但新增回归测试本身无法编译，因此不能宣布安卓测试通过或P0全部验收完成。另有工程在干净机器上不能自行启动构建的问题。

## 1. [P1] 新增回归测试有可空类型错误，整个安卓测试任务失败

- 文件：`android/app/src/test/java/com/tutorialcoach/app/ui/screens/plan/PlanViewModelTest.kt:78,122`。
- 第78行 `_session = MutableStateFlow(makeSession())` 推断为 `MutableStateFlow<DomainSession>`；第122行使用安全调用 `_session.value?.copy(...)` 得到 `DomainSession?`，不能赋值给非空类型。
- 实际命令：`gradlew.bat --no-daemon :app:testDebugUnitTest :app:assembleDebug --offline --console=plain`。
- 实际结果：`:app:compileDebugUnitTestKotlin FAILED`；`PlanViewModelTest.kt:122:30 Assignment type mismatch: actual type is DomainSession?, but DomainSession was expected.`
- 影响：新回归测试以及本次安卓测试套件均未实际执行，不能继续沿用上轮11项通过的结论作为当前提交的证明。
- 修复方向：测试网关若需模拟空会话，显式声明 `MutableStateFlow<DomainSession?>(makeSession())`；若始终非空，则使用非空copy。依据测试目的选定类型，再运行完整测试任务。此处不需要改业务逻辑。

## 2. [P2] 提交的gradlew依赖个人缓存与机器路径，干净机器无法复现构建

- 文件：`android/gradlew.bat:5–15`；`android/gradlew:11–25`；`android/gradle.properties:1`。
- gradlew不是标准Gradle Wrapper启动器，而是扫描本机 `.gradle/wrapper/dists/gradle-8.9-bin`，没有缓存则直接退出。Git中没有 `android/gradle/wrapper/gradle-wrapper.jar` 与 `gradle-wrapper.properties`。gradle.properties还将运行JDK固定到本机 `D:/Java/ideaIU-2025.2.win/jbr`。
- 影响：评委/其他开发者首次克隆项目，即便已安装合适JDK与Android SDK，仍无法通过项目gradlew下载并启动指定Gradle；必须先复制作者缓存并处理D盘绝对路径。这违反可复现工程交付目标。
- 修复方向：用已可用的Gradle生成标准Wrapper，提交jar/properties及启动脚本，固定8.9与校验和；将本机JDK路径保留在未提交的本地配置/会话环境中，README说明JDK要求。保留本机缓存作为加速，不能作为唯一启动方式。
- 证据：本轮 `git ls-files android/gradle android/gradlew android/gradlew.bat` 仅列version catalog与两份自制脚本；直接检查脚本的无缓存退出分支和绝对路径。未更改本机缓存或系统配置。

## 上轮恢复逻辑复查

- PlanViewModel的succeeded分支先设置pendingPlanSessionId再fetchPlan；GET失败保留pending。
- retry/generate/dismiss入口遇到pending时只重新获取计划。
- SessionRepository.loadPlan成功后同步currentPlanVersion，并检查会话ID再写入计划。
- 独立审查者交叉核对后未发现此修复分支的确定性新缺陷。
- 新回归测试的断言方向正确（createCalls=1、loadCalls=2、Ready），但需先修复其编译错误才能成为验证证据。

## 本轮验证

| 项目 | 结果 |
|---|---|
| 服务端 `python -m pytest -q` | 21项通过 |
| 安卓 `testDebugUnitTest` | 测试源码编译失败；未通过 |
| 单独 `assembleDebug` | BUILD SUCCESSFUL in 9s；当前源码产物约10.5MB |
| 密钥扫描 `scripts/scan_secrets.py` | 108个文件，无匹配；Git未跟踪server/.env |
| 真机安装/交互/断网恢复 | 本轮未执行；仍需设备验收 |
| GitHub远程HEAD核验 | 本轮连接被重置，未重新确认；本地已存在3个应用/文档提交，不再是未提交源码 |

APK：`android/app/build/outputs/apk/debug/app-debug.apk`。APK构建通过不等于安卓测试或真机验收通过。

## 给码道的下一条任务

请读取 docs/CODEX_P0_CODE_REVIEW_ROUND3.md，只处理两项审查问题，不进入P1：先修复PlanViewModelTest的可空类型，让完整安卓单测实际执行；再生成并提交标准Gradle Wrapper，移除受版本管理的个人JDK绝对路径，保留本地环境可用。重新运行服务端测试、安卓testDebugUnitTest与assembleDebug，准确记录测试数/构建结果/设备验收状态，更新阶段报告。不得修改秘密配置或上传密钥。完成后报告修改、验证和Git状态，暂停复审。
