# Android 构建状态（P0/D1）

## 工具链

- 会话级 JBR 21.0.7；Gradle 8.9。
- `bash ./gradlew --version` PASS，见 `gradle_version.txt`。
- 未修改系统 `JAVA_HOME`/PATH。

## Codex 复审环境中的真实构建

- 2026-11-04T15:58Z（Asia/Shanghai 23:58），Codex 在普通终端执行：
  `gradlew.bat :app:testDebugUnitTest :app:assembleDebug --console=plain`
  结果：`BUILD SUCCESSFUL in 27s`。
- 产物：`android/app/build/outputs/apk/debug/app-debug.apk`（约 10 MB）。
- APK 核验：`aapt2 dump badging` 显示
  `package='com.tutorialcoach.app' versionCode='1' versionName='0.1.0'`，
  minSdk 26 / targetSdk 35 / INTERNET 权限；见 `android_apk_info.txt`。
- JVM 测试：DtoTest 3、ErrorMapperTest 4、PlanValidatorTest 4，共 11 项通过；
  见 `android_test_results.txt`。

## 码道沙箱的限制（不代表工程配置失败）

- 在码道本会话中，`assembleDebug` 多次无法执行：命令不产生日志、无进程输出；
  尝试过本地 `gradlew`、Java `@argfile`、PowerShell、`--no-daemon`/离线等方式。
- 这是执行环境拦截；Codex 复审环境已证明工程可构建。
- 因此“构建成功”只归因于 Codex 的独立验证，不写成码道本会话执行成功。

## 重要时序说明

- 上述 APK 构建发生在第二轮审查项（PlanViewModel 计划获取失败恢复）修复之前。
- 修复后又新增 `PlanViewModelTest`；因此当前源码尚未重新构建/测试。
- 需要复审/用户在普通终端重新执行：
  ```powershell
  cd android
  $env:JAVA_HOME = 'D:\Java\ideaIU-2025.2.win\jbr'
  .\gradlew.bat --no-daemon :app:testDebugUnitTest :app:assembleDebug
  ```
  预期 APK 覆盖同一路径。

## 安装/启动

- `adb devices` 为空，无 AVD，系统镜像仅安装器残留。
- 因此真机安装、启动、截图与设备端 UI 验收 **BLOCKED**。