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

`adb devices -l` 为空，无 AVD，系统镜像仅安装器残留。

结论：真机安装、启动、截图、实际 UI 操作、断网恢复仍为 **BLOCKED**，不能用构建成功代替设备验收，P0 未全部完成。