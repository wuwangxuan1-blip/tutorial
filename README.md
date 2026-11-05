# tutorial
华为大赛项目

## 实践陪练 Android App

用户输入目标，应用结合现有材料、设备和经验提供步骤指导，并接收图片或短片反馈。覆盖烹饪烘焙、摄影与相机运镜、软件技能、咖啡饮品。

当前状态（P1/D2）：共享契约样例与双端解析、烹饪两轮澄清/可选跳过、真实模型计划、异常与恢复、真机复测已完成；服务端 44 项测试、安卓 19 项 JVM 测试通过，debug APK 已构建（约 11 MB）。真机（realme GT6）完成两轮澄清、含假设计划、步骤卡；旋转/切后台/进程恢复等健壮性未验证。D2 完成，等待 Codex 复审。

- 项目入口：[PROJECT_PLAN.md](PROJECT_PLAN.md)
- 文档索引：[docs/README.md](docs/README.md)
- 实现状态：[docs/IMPLEMENTATION_STATUS.md](docs/IMPLEMENTATION_STATUS.md)
- 环境实测：[docs/ENVIRONMENT.md](docs/ENVIRONMENT.md)
- 码道任务：[docs/CODEARTS_PROMPTS.md](docs/CODEARTS_PROMPTS.md)
- 证据目录：[codearts_proof/day1/](codearts_proof/day1/)、[codearts_proof/day2/](codearts_proof/day2/)
- 契约样例：[contracts/examples/](contracts/examples/)

## 环境要求

- JDK 21（本机使用 JBR 21.0.7；Gradle 8.9 不能用默认 JDK 25 运行）。
- Android SDK：platform 35、build-tools 36.0.0、platform-tools；compileSdk/targetSdk 35，minSdk 26。
- Python 3.12。
- 可选：ffmpeg/ffprobe 7.x（后续媒体阶段使用）。

## 本地配置（不提交）

- `server/.env`：从 `server/.env.example` 创建，填写 DeepSeek 配置；只保存在服务端，不进入 APK/Git/日志。
- `android/local.properties`：填写本机 SDK 路径，例如：
  ```properties
  sdk.dir=C\:\\Users\\<user>\\AppData\\Local\\Android\\Sdk
  ```
  该文件被 `.gitignore` 忽略。
- JDK 不写入 `android/gradle.properties`；构建时使用会话级 `JAVA_HOME`。不要修改系统环境变量。

## 首次构建 Android

Windows PowerShell：

```powershell
$env:JAVA_HOME = 'C:\path\to\jdk-21'
cd android
.\gradlew.bat --version
.\gradlew.bat --no-daemon :app:testDebugUnitTest :app:assembleDebug
```

Linux/macOS：

```bash
export JAVA_HOME=/path/to/jdk-21
cd android
./gradlew --version
./gradlew --no-daemon :app:testDebugUnitTest :app:assembleDebug
```

产物：`android/app/build/outputs/apk/debug/app-debug.apk`。

Gradle Wrapper 固定 Gradle 8.9，官方发行地址与 SHA-256 校验和见 `android/gradle/wrapper/gradle-wrapper.properties`。首次构建可能需要联网下载 Gradle 发行版与 Maven 依赖；本机已有缓存可作为加速，但不是唯一启动方式。

## 启动服务端

```powershell
cd server
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

真机联调：

```powershell
adb reverse tcp:8000 tcp:8000
```

APK 通过 `http://127.0.0.1:8000` 访问服务端；Key 只在服务端 `.env`。

## P0 范围与边界

- 只实现烹饪领域的最小真实垂直流程；其它三个领域保留在契约/枚举中，计划生成在后续阶段开放。
- 不包含完整计时、媒体反馈、运镜动画、配方与参考教程导入。
- 无设备时安装/启动/截图明确标记 BLOCKED，不以构建成功代替真机验收。
- 真实模型结果、测试、构建与证据均不得伪造；证据见 `codearts_proof/day1/`。