# Android 构建与测试状态（P0/D1，第三轮）

## 标准 Wrapper

- 使用本机 Gradle 8.9 生成标准 Wrapper：
  - `android/gradlew`
  - `android/gradlew.bat`
  - `android/gradle/wrapper/gradle-wrapper.jar`
  - `android/gradle/wrapper/gradle-wrapper.properties`
- 固定官方发行地址：
  `https://services.gradle.org/distributions/gradle-8.9-bin.zip`
- 官方 SHA-256：
  `d725d707bfabd4dfdc958c624003b3c80accc03f7037b5122c4b1d0ef15cecab`
- 生成 `:wrapper` 时网络校验失败（无法访问 services.gradle.org），使用 `--no-validate-url` 生成后，在 properties 中恢复 `validateDistributionUrl=true`；运行时仍按官方地址和 SHA-256 校验。
- `android/gradle.properties` 已移除 `org.gradle.java.home` 个人绝对路径；构建使用会话级 `JAVA_HOME=JBR 21.0.7`。
- `bash ./gradlew --version` 真实通过（Gradle 8.9 / Launcher JVM 21.0.7）。

## 安卓单元测试

命令：

```bash
export JAVA_HOME=D:/Java/ideaIU-2025.2.win/jbr
cd android
bash ./gradlew --no-daemon :app:testDebugUnitTest --console=plain
```

结果：`BUILD SUCCESSFUL in 15s`。

| 测试套件 | 数量 | 失败 | 错误 | 跳过 |
|---|---:|---:|---:|---:|
| DtoTest | 3 | 0 | 0 | 0 |
| ErrorMapperTest | 4 | 0 | 0 | 0 |
| PlanValidatorTest | 4 | 0 | 0 | 0 |
| PlanViewModelTest | 1 | 0 | 0 | 0 |
| **合计** | **12** | **0** | **0** | **0** |

新增的 `PlanViewModelTest` 实际执行并通过，覆盖：
- Job 成功后第一次 GET 计划失败；
- 重试只重新 GET 原计划，不创建新 Job（createCalls=1、loadCalls=2）；
- 最终进入 Ready；
- 计划版本同步为 1。

## APK 构建

命令：

```bash
bash ./gradlew --no-daemon :app:assembleDebug --rerun-tasks --console=plain
```

结果：`BUILD SUCCESSFUL in 28s`，35 个任务全部执行。

产物：`android/app/build/outputs/apk/debug/app-debug.apk`（约 10 MB，2026-11-05 01:01）。

`aapt2 dump badging` 核验：
- package `com.tutorialcoach.app`
- versionName `0.1.0`
- minSdk 26 / targetSdk 35 / compileSdk 35
- INTERNET 权限
- label `实践陪练`

## 设备安装

- 设备：realme GT6 / RMX3800，Android 16，adb 序列号 `eeffd16b`，状态 `device`。
- `adb install -r app-debug.apk`：`Success`。
- 冷启动成功；首页、澄清 5 问、真实模型 5 步计划、步骤卡 1/5→2/5、诊断页、跨会话隔离、断网恢复均通过。
- 截图保存在本地 `device_home.png`、`device_step.png`，未提交。
- 未测试：旋转、切后台、进程被杀恢复、中文输入、第二份计划生成。

结论：真机最小垂直流程 **PASS**；更完整的健壮性验证仍待后续补充，不据此宣称所有设备场景通过。