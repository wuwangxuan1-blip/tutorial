# D3 实际命令（摘录）

## 服务端

```text
cd server
.venv/Scripts/python.exe -m pytest -o addopts=""
→ 71 passed
```

## Android

```powershell
$env:JAVA_HOME='D:\Java\ideaIU-2025.2.win\jbr'
cd android
.\gradlew.bat --no-daemon --rerun-tasks :app:testDebugUnitTest :app:assembleDebug
→ BUILD SUCCESSFUL in 42s
→ 41 actionable tasks: 41 executed
```

## 真机

```text
adb devices -l
→ eeffd16b device product:RMX3800 model:RMX3800 device:RE5C4FL1

adb reverse tcp:8000 tcp:8000
adb install -r android/app/build/outputs/apk/debug/app-debug.apk
→ Success
adb shell am start -n com.tutorialcoach.app/.MainActivity
```

服务端按 `server/.env` 启动真实 FastAPI + DeepSeek；未打印或提交 Key。

## 真实模型流程

- 软件：App 内创建会话、两轮内澄清、生成计划（5 步 v1）、步骤提问、条件修订（一次应用、一次拒绝）。
- 烹饪：服务端 API 创建 `sess_01M6NJ7TMDHPXR5GRWPV8CCGP7`，真实模型生成 5 步计划，过敏通用提示存在。