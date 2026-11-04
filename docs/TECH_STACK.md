# 技术选型与工程结构

> 状态：规划选型，2026-11-04。本文包含只读环境检查结果和明确标注的“未验证”项；不要把“已安装/已缓存”当成“构建已通过”。
> 契约细节见 [API_CONTRACT.md](API_CONTRACT.md)；产品范围见 [PRODUCT_REQUIREMENTS.md](PRODUCT_REQUIREMENTS.md)。

## 1. 选型结论

### 1.1 推荐

**原生 Android：Kotlin + Jetpack Compose；服务端：Python 3.12 + FastAPI；模型：DeepSeek OpenAI 兼容 API（服务端持有 Key）；媒体：ffmpeg/ffprobe 子进程；存储：本地 JSON 文件 + 原子写。**

选择理由：

1. 本机已有 JDK 21（IntelliJ JBR）、Android SDK、Gradle 发行版缓存、ffmpeg；没有 Flutter/React Native 工具链，七天不适合引入新的跨端构建链。
2. 原生 API 直接覆盖 Photo Picker、`MediaMetadataRetriever`、`VideoView`、Compose Canvas；运镜动画和媒体选择不需要插件桥接。
3. APK 是硬要求；原生 Gradle 构建路径最短，问题可定位。
4. Python 服务端便于调用 DeepSeek、ffmpeg、PDF/DOCX 解析；单进程即可演示，不引入数据库/队列。
5. 四领域是内容/校验差异，不需要四套客户端架构；单 module + 手写 DI 足够。

### 1.2 方案比较

评分 1–5，5 最好；权重按七天单人比赛项目。

| 方案 | 本机工具链 | 媒体能力 | 动画/绘图 | APK/安装 | 七天风险 | 可维护性 | 结论 |
|---|---|---|---|---|---|---|---|
| 原生 Kotlin + Compose + FastAPI | 5（JDK/SDK/Gradle 已有，缺 build-tools 35） | 5 | 5（Canvas） | 5 | 4 | 4 | **推荐** |
| Flutter + Dart + FastAPI | 1（未安装 Flutter/Dart） | 4 | 4 | 4 | 2（新工具链/插件） | 4 | 不推荐本期 |
| React Native/Expo + FastAPI | 1（未安装 Node/RN） | 3（媒体/视频插件） | 3 | 3（Expo 构建链） | 2 | 3 | 不推荐本期 |
| 纯 Web/PWA | 5 | 2 | 4 | 0（不是 APK） | 1 | 3 | 违反硬要求，排除 |
| WebView 套壳 | 4 | 2 | 3 | 3 | 2 | 2 | 违反“不是套壳”要求，排除 |
| 端侧本地大模型 | 1（无模型/显存/下载预算） | 2 | 4 | 3 | 1 | 2 | 不可行；且用户只有 DeepSeek API |

### 1.3 为什么不是“全本地/无服务端”

- 用户只有 DeepSeek 官网 API，没有可打包的模型权重；APK 不能携带 Key。
- 视频抽帧、PDF/DOCX 解析、模型调用放服务端更容易统一校验、记录和重试。
- 服务端在本机运行、手机通过 `adb reverse` 访问，仍是可演示的完整 Android 应用；不是网页套壳。
- 代价：评委只安装 APK 不能独立工作；必须在 README/演示视频中说明“APK + 本机服务端 + 用户 Key”。
- **部署决策尚未由用户确认**：本地 FastAPI + `adb reverse` 是开发与比赛演示路径，不是已确认的最终产品形态。面向真实用户的服务端部署（云/局域网/内网）不在本期，需用户后续决定；不得声称单独安装 APK 即可联网使用。

## 2. 本机环境实测（2026-11-04，只读）

> 这是快照；CodeArts 首日必须复测并写 `docs/ENVIRONMENT.md`。未执行的构建/安装/模型调用不得写成成功。

| 项目 | 实测结果 | 影响 |
|---|---|---|
| OS | Windows 11 Home China 10.0.26200 | PowerShell 为主；脚本用 `.ps1` |
| 默认 Java | JDK 25.0.2，`JAVA_HOME=D:\Java\jdk-25.0.2` | **Gradle 8.9/8.10 不支持 Java 25 运行**；必须用 JBR 21 |
| 可用 JDK 21 | IntelliJ IDEA Ultimate 2025.2 自带 JBR 21.0.7：`D:\Java\ideaIU-2025.2.win\jbr` | 项目级 Gradle JDK；不改系统 `JAVA_HOME`/PATH |
| Gradle | 不在 PATH；`~/.gradle/wrapper/dists` 已缓存 8.9、8.10.2、9.2.1 | 用 8.9 本地发行版生成 wrapper；不依赖网络下载 |
| Android Studio | 未发现 | 用 Gradle CLI + IntelliJ IDEA；不依赖预览 |
| Android SDK | `C:\Users\wwx\AppData\Local\Android\Sdk` | 已装 platforms 34/35、platform-tools 37.0.0、emulator 36.6.11 |
| Build Tools | 34.0.0、36.0.0；**35.0.0 缺失** | AGP 8.7 默认需要 35；先试 36，失败需用户批准安装 35 |
| 系统镜像 | `system-images/android-34/google_apis/x86_64` 只有 `.installer/.installData`，`sdkmanager --list_installed` 无 system-images | **没有可用系统镜像**；不能声称模拟器可用 |
| AVD/真机 | `emulator -list-avds` 为空；`adb devices` 无设备 | D1 APK 安装/启动闸门当前受阻；需真机或经批准安装镜像 |
| 虚拟化 | WHPX 已安装且可用 | 若安装系统镜像，模拟器有运行基础；仍需实测 |
| sdkmanager | 12.0 警告只理解 SDK XML v3（遇到 v4）；`--list_installed` 可运行 | 安装新组件可能失败；不得假设安装成功 |
| AGP 缓存 | 8.5.0、8.7.3、9.0.0；**8.8.2 未缓存** | 主方案 8.7.3（已缓存）；8.8.2 仅备选 |
| Kotlin/Compose 缓存 | Kotlin 2.0.21、Compose BOM 2024.12.01、OkHttp 4.12.0、Coil 2.7.0 已缓存 | 减少下载；仍需构建验证 |
| Python | 3.12.9（miniconda），pip 25.0 | 项目 `.venv`；不污染全局 |
| Python 包 | numpy 2.2.6、Pillow 12.2.0、pydantic 2.10.3 已装；fastapi/uvicorn/httpx 未装 | D1 建 venv 安装并锁版本 |
| ffmpeg | 7.0.2（gyan.dev full build）；`vidstabdetect`、`vidstabtransform`、`vmafmotion` 过滤器存在 | 视频抽帧/运动估计可用；不装 OpenCV |
| 网络 | DeepSeek API 可达（无 Key 返回 401）；PyPI/Google Maven/Maven Central 可达；Google Maven 较慢 | 依赖可下载；优先用缓存 |
| DeepSeek Key | 当前 shell 无 `DEEPSEEK_API_KEY` | 探针只能明确 `NO_KEY`；不得伪造成功 |
| Git/GitHub | 项目目录无 `.git`；无 `gh`、无 SSH key、无 GitHub 凭据、无 remote；GCM 二进制存在但无 GitHub 账号 | 本地可初始化；**当前不能推送 GitHub**；需用户提供仓库/登录 |
| 项目现状 | CC_TASK.md、START_CODEARTS.md、PROJECT_PLAN.md、`.codeartsdoer`/`.arts` 配置和 docs | 本次只写文档；不覆盖现有文件 |

### 2.1 已用官方/Maven 元数据核实

- Compose BOM `2024.12.01`、AGP `8.7.3`/`8.8.2`、Kotlin `2.0.21`、activity-compose `1.9.3`、lifecycle `2.8.7`、navigation-compose `2.8.5`、OkHttp `4.12.0`、Coil `2.7.0`、kotlinx-serialization-json `1.7.3` 的 POM HEAD 返回 200。**8.8.2 仅核实存在，不是选型；主方案是已缓存的 8.7.3（见 3.1）。**
- 另核实 lifecycle-runtime-compose `2.8.7`、core-ktx `1.15.0`、material3 `1.3.1`、ui-test-junit4 `1.7.6`。
- “坐标存在”不等于“本机构建通过”；D1 以 `assembleDebug` 为准。
- AGP 8.7.3 的 JAR/POM 已在本机 Gradle 缓存；AGP 8.8.2 不在缓存。

## 3. 版本锁定

### 3.1 Android

| 组件 | 版本 | 说明 |
|---|---|---|
| Gradle | **8.9** | 本机已缓存；与 AGP 8.7.3 匹配；运行在 JBR 21 |
| AGP | **8.7.3** | 已缓存；支持 compileSdk 35、JDK 17+；默认 build-tools 35 |
| JDK（Gradle 运行） | **JBR 21.0.7** | 会话级 `JAVA_HOME` + `org.gradle.java.home`；不改系统 |
| Kotlin | **2.0.21** | 与 Compose 编译器插件同版本 |
| Compose 编译器插件 | `org.jetbrains.kotlin.plugin.compose` **2.0.21** | Kotlin 2.0+ 必需 |
| Compose BOM | **2024.12.01** | 统一 Compose 依赖 |
| compileSdk / targetSdk | **35 / 35** | platforms 35 已装 |
| minSdk | **26** | 覆盖目标设备；避免旧 API 分支 |
| Build Tools | **35.0.0**（首选；缺失，需批准安装）或 **36.0.0**（先实测） | 不得假设 36 一定被 AGP 接受 |
| Java/Kotlin target | **17** | AGP 8.x 要求 JDK 17+；JBR 21 可编译 target 17 |
| applicationId | `com.tutorialcoach.app` | 首次提交前锁定；改名需全局同步 |
| versionCode / versionName | `1` / `0.1.0` | 提交版可升到 `1.0.0` |

Android 依赖（精确版本；由 version catalog 管理）：

| 依赖 | 版本 | 用途 |
|---|---|---|
| `androidx.core:core-ktx` | 1.15.0 | 基础 |
| `androidx.activity:activity-compose` | 1.9.3 | Compose Activity |
| `androidx.lifecycle:lifecycle-runtime-compose` | 2.8.7 | `collectAsStateWithLifecycle` |
| `androidx.lifecycle:lifecycle-viewmodel-compose` | 2.8.7 | ViewModel |
| `androidx.navigation:navigation-compose` | 2.8.5 | 导航 |
| Compose BOM | 2024.12.01 | `ui`、`material3`、`ui-tooling`、`ui-test-*` |
| `org.jetbrains.kotlinx:kotlinx-serialization-json` | 1.7.3 | DTO |
| `org.jetbrains.kotlinx:kotlinx-coroutines-android` | 1.9.0 | 协程 |
| `com.squareup.okhttp3:okhttp` | 4.12.0 | HTTP |
| `io.coil-kt:coil-compose` | 2.7.0 | 图片缩略图 |
| `junit:junit` | 4.13.2 | 单元测试 |
| `org.jetbrains.kotlinx:kotlinx-coroutines-test` | 1.9.0 | 协程测试 |
| `com.squareup.okhttp3:mockwebserver` | 4.12.0 | API 测试 |
| Compose `ui-test-junit4` | BOM | 设备 UI 测试（可用时） |

不使用：Hilt、Room、KSP、WorkManager、Media3、Retrofit、DataStore、OpenCV、任何动态版本（`+`、`latest.release`）。

### 3.2 服务端

| 组件 | 版本策略 |
|---|---|
| Python | 3.12.9 |
| FastAPI | `>=0.115,<1.0`；D1 安装后锁精确版本 |
| uvicorn | `[standard] >=0.32,<1.0` |
| httpx | `>=0.28,<1.0` |
| Pydantic | `>=2.10,<3.0`（本机已有 2.10.3） |
| python-multipart | `>=0.0.12,<1.0` |
| pypdf | `>=5.1,<6.0` |
| python-docx | `>=1.1,<2.0` |
| beautifulsoup4 | `>=4.12,<5.0` |
| Pillow | `>=11,<13`（本机 12.2.0） |
| numpy | `>=2.0,<3.0`（本机 2.2.6；仅统计） |
| python-dotenv | `>=1.0,<2.0` |
| pytest / pytest-asyncio | `>=8.3,<9.0` / `>=0.24,<1.0` |
| ffmpeg/ffprobe | 7.0.2 外部依赖；不打包进 APK/仓库 |

- `requirements.in` 写范围；D1 `pip freeze > requirements.txt` 锁精确版本并提交。
- 不安装 OpenCV；运动估计用 ffmpeg `vidstabdetect`/`vmafmotion` + Python 统计。
- ffmpeg 为 GPL 构建，仅作为外部可执行文件调用；README 记录许可证，不静态链接/分发二进制到 APK。

### 3.3 模型

| 配置 | 默认 | 说明 |
|---|---|---|
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | OpenAI 兼容 Chat Completions |
| `DEEPSEEK_API_KEY` | 无默认 | 仅服务端 `.env`；不得写入 APK/Git/日志 |
| `DEEPSEEK_TEXT_MODEL` | `deepseek-flash` | 文本/计划/提问 |
| `DEEPSEEK_VISION_MODEL` | `deepseek-flash` | 官方文档称支持 text+image；**必须 D1 探针验证** |
| `DEEPSEEK_TIMEOUT_S` | `90` | 异步 Job 的每次模型请求超时 |
| `DEEPSEEK_ASK_TIMEOUT_S` | `45` | `POST /ask` 的模型请求超时 |
| `ASK_ENDPOINT_TIMEOUT_S` | `60` | `POST /ask` 端点总预算；超时返回 504 |
| `JOB_TIMEOUT_S` | `180` | 异步 Job 总预算（含一次修复重试） |
| `MODEL_MAX_CONCURRENCY` | `2` | 单进程内信号量 |

- 官方文档：`deepseek-flash` 支持文本和图片；`deepseek-v4-pro` 仅文本；官方文档未列出视频输入，本项目按“不支持直接视频输入、服务端抽帧”处理，并由 D1 探针记录实际结果，不把任何模型能力当已验证事实。
- 超时分层见 [API_CONTRACT.md](API_CONTRACT.md) 1.3；Android 提问读取 75s，服务端 60s 内必须返回；Job 通过轮询，不让 HTTP 请求长时间挂着。
- 不依赖工具调用；主流程用 `response_format={"type":"json_object"}` + Pydantic 校验 + 一次修复重试。工具调用只探测记录，不作为架构前提。
- 模型名/视觉能力/JSON 行为均为“待 D1 真实探针”；不能把文档描述当成本账户可用。

## 4. 架构

```text
Android (Kotlin/Compose)
  │  HTTP/JSON + multipart
  ▼
FastAPI (Python 3.12, single process, 127.0.0.1:8000)
  ├─ Routers: health/sessions/plans/progress/media/feedback/revisions/recipes/references/jobs
  ├─ Services: model_client, plan_service, feedback_service, revision_service,
  │            reference_service, media_service, recipe_service, job_service
  ├─ Storage: JSON files + atomic writes + per-session locks
  ├─ Media: ffprobe/ffmpeg (frames, vidstabdetect), Pillow (image normalize)
  └─ DeepSeek API (text + image only; key server-side)
```

### 4.1 模块边界

Android 单 module，包 `com.tutorialcoach.app`：

```text
app/src/main/java/com/tutorialcoach/app/
  MainActivity.kt
  TutorialCoachApp.kt
  di/AppContainer.kt
  data/
    ApiClient.kt
    Dto.kt
    SessionRepository.kt
    MediaRepository.kt
    LocalStore.kt
  domain/
    Model.kt
    PlanValidator.kt
    CameraMoveValidator.kt
    TimerEngine.kt
    ErrorMapper.kt
  ui/
    theme/
    navigation/
    screens/home|clarify|plan|step|feedback|revision|records|recipe|settings/
    components/StepCard.kt, CameraPathCanvas.kt, ErrorBanner.kt
```

服务端：

```text
server/app/
  main.py
  config.py
  api/
    health.py sessions.py plans.py progress.py media.py feedback.py
    revisions.py recipes.py references.py jobs.py
  models/
    common.py session.py plan.py camera.py feedback.py revision.py
    recipe.py media.py reference.py job.py
  services/
    model_client.py prompt_builder.py plan_service.py feedback_service.py
    revision_service.py reference_service.py media_service.py
    recipe_service.py job_service.py store.py security.py ffmpeg.py
  prompts/
    system.txt plan_cooking.txt plan_photography.txt plan_software.txt
    plan_coffee.txt feedback.txt revision.txt ask.txt
  storage/ (runtime; ignored)
server/tests/
```

### 4.2 依赖方向

- UI → ViewModel → Repository → ApiClient/LocalStore；UI 不直接发 HTTP。
- domain 只依赖 Kotlin 标准库/协程；不依赖 Android UI/OkHttp。
- 服务端 router → service → model/store；router 不写业务规则。
- 契约 DTO 只在 `data/Dto.kt` 与服务端 `models/`；domain 模型单独映射，避免网络字段泄漏到 UI。

## 5. 目录结构

```text
tutorial-coach/
  PROJECT_PLAN.md
  README.md
  docs/
    README.md
    PRODUCT_REQUIREMENTS.md
    TECH_STACK.md
    API_CONTRACT.md
    CODING_STANDARDS.md
    IMPLEMENTATION_PLAN.md
    CODEARTS_PROMPTS.md
    COMPETITION_CHECKLIST.md
    RISK_REGISTER.md
    ENVIRONMENT.md            # CodeArts D1 创建，记录复测
    IMPLEMENTATION_STATUS.md  # CodeArts 每阶段更新
  android/
    settings.gradle.kts
    build.gradle.kts
    gradle.properties
    gradle/libs.versions.toml
    gradle/wrapper/gradle-wrapper.properties
    gradlew / gradlew.bat
    local.properties         # 本机生成；不提交
    app/
      build.gradle.kts
      src/main/AndroidManifest.xml
      src/main/java/com/tutorialcoach/app/...
      src/main/res/...
      src/test/...
      src/androidTest/...
  server/
    app/...
    tests/...
    requirements.in
    requirements.txt
    .env.example
  contracts/examples/
  scripts/
    setup-server.ps1
    run-server.ps1
    build-apk.ps1
    install-apk.ps1
    verify-submission.ps1
  codearts_proof/
    README.md
    day1/ ... day7/
    summary.md
  submission/
    ppt/
    readme/
    video/                   # 大文件默认不提交；按比赛要求单独打包
```

## 6. Android 构建、安装、运行

### 6.1 会话级 JDK 21（不修改系统）

PowerShell：

```powershell
$env:JAVA_HOME = 'D:\Java\ideaIU-2025.2.win\jbr'
$env:Path = "$env:JAVA_HOME\bin;$env:Path"
java -version
```

期望：`openjdk version "21.0.7"`。如果仍是 25，停止构建，检查会话变量。

项目 `android/gradle.properties`：

```properties
org.gradle.java.home=D:/Java/ideaIU-2025.2.win/jbr
org.gradle.jvmargs=-Xmx2g -Dfile.encoding=UTF-8
android.useAndroidX=true
android.nonTransitiveRClass=true
kotlin.code.style=official
```

- `org.gradle.java.home` 只影响 Gradle daemon；`gradlew.bat` 启动 JVM 仍读 `JAVA_HOME`，所以两者都要设置。
- 不把 `JAVA_HOME` 写进系统环境；不修改 PATH 系统变量。

### 6.2 Wrapper

Gradle 不在 PATH，但 8.9 已缓存。CodeArts 在 `android/` 创建最小 `settings.gradle.kts` 后，用缓存发行版生成 wrapper：

```powershell
$gradle = "$env:USERPROFILE\.gradle\wrapper\dists\gradle-8.9-bin\90cnw93cvbtalezasaz0blq0a\gradle-8.9\bin\gradle.bat"
& $gradle wrapper --gradle-version 8.9 --distribution-type bin
```

- 目录哈希可能因缓存副本不同而不同；用 `Get-ChildItem` 找到实际 `gradle.bat`，不要把哈希写死为唯一路径。
- `gradle-wrapper.properties` 固定 `distributionUrl=https\://services.gradle.org/distributions/gradle-8.9-bin.zip`；有缓存时可离线。
- 若 wrapper 生成失败，记录真实错误；不要改用 Gradle 9.x/AGP 9.x。

### 6.3 build-tools 35 的处理顺序

1. 先用已安装的 **36.0.0** 显式构建：`android/app/build.gradle.kts` 设 `buildToolsVersion = "36.0.0"`。
2. 若 AGP 接受且 `assembleDebug` 成功：记录版本与日志；仍需在 README 说明。
3. 若 AGP 报缺少/不兼容 35：**请求用户批准**安装 `build-tools;35.0.0`：

```powershell
& "$env:LOCALAPPDATA\Android\Sdk\cmdline-tools\latest\bin\sdkmanager.bat" "build-tools;35.0.0"
```

4. 安装后 `sdkmanager --list_installed` 确认；再构建。
5. 不得假定 36 一定兼容，也不得静默改 SDK/系统设置。

### 6.4 构建与安装

```powershell
cd C:\Users\wwx\Documents\Codex\2026-11-04\w\outputs\tutorial-coach\android
.\gradlew.bat --version
.\gradlew.bat :app:assembleDebug
```

期望：

- `--version` 显示 `Gradle 8.9`、`JVM 21.0.7`。
- 构建成功；APK：`android/app/build/outputs/apk/debug/app-debug.apk`。
- 失败时保存 `codearts_proof/day1/build.log`（脱敏），记录真实错误；不得用“应该可以”代替。

安装/启动：

```powershell
adb devices
adb install -r .\app\build\outputs\apk\debug\app-debug.apk
adb shell am start -n com.tutorialcoach.app/.MainActivity
```

- 当前 `adb devices` 为空；D1 必须由用户连接真机（开启 USB 调试）或批准安装系统镜像并创建 AVD。否则 APK 安装/启动闸门标记 **BLOCKED**，不能写 PASS。
- 模拟器路径（仅在用户批准安装镜像后）：

```powershell
sdkmanager "system-images;android-34;default;x86_64"
avdmanager create avd -n tutorialcoach_api34 -k "system-images;android-34;default;x86_64" -d pixel_6
emulator -avd tutorialcoach_api34
```

  - `system-images;android-34;google_apis;x86_64` 目录当前只有安装器残留，不是可用镜像；不得直接创建 AVD。
  - `sdkmanager` 12.0 的 XML 警告可能导致安装失败；失败时记录原始输出，不自行改 SDK 元数据。

### 6.5 服务端连接

```powershell
adb reverse tcp:8000 tcp:8000
```

- 服务端只监听 `127.0.0.1:8000`；手机访问 `http://127.0.0.1:8000`，由 adb 转发到开发机。
- 无 USB 时才考虑 LAN：服务端 `--host 0.0.0.0`、Windows 防火墙放行、手机改 LAN IP；这是非默认路径，需用户明确同意并承担暴露风险。
- 不提供公网部署/账号体系。

### 6.6 Release 签名

- 本期交付 debug APK；不发布商店。
- 若后续需要 release：keystore 放仓库外，密码用环境变量/本机密钥库；不得提交 `*.jks`/`*.keystore`；不在文档/日志/截图出现密码。
- 没有用户明确要求，不生成/上传 release 到商店。

## 7. 服务端启动与部署

```powershell
cd C:\Users\wwx\Documents\Codex\2026-11-04\w\outputs\tutorial-coach\server
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
# 用户手工编辑 .env，填入 DEEPSEEK_API_KEY；不要把 Key 贴到聊天/日志
uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
```

- `--workers 1`：Job 注册表在进程内；多 worker 会丢 Job。
- 不使用 `--reload` 演示：reload 会重启进程并终止 Job。
- `.env` 不提交；`.env.example` 只放占位符。
- 健康检查：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/v1/health
```

- 期望 HTTP 200；无 Key 时 `status=degraded`，所有检查为 true 时才是 `ok`；`model_configured` 取决于 Key，不得把 false 伪装成 true。
- 数据目录 `server/data/` 运行时可写；启动时创建；不提交。
- 日志：控制台 + `server/data/logs/app.log`（脱敏）；不记录 Key/base64/用户原文。

### 7.1 数据文件布局

```text
server/data/
  sessions/{session_id}.json
  plans/{session_id}/{version}.json
  jobs/{job_id}.json
  feedback/{feedback_id}.json
  revisions/{revision_id}.json
  recipes/{recipe_id}.json
  media/{media_id}.{ext}
  references/{reference_id}.json
  idempotency/{hash}.json
  logs/
```

- 原子写：写临时文件 `*.tmp` → `os.replace`；同一会话/文件用 `asyncio.Lock`。
- Job 状态持久化；启动时把 `queued/running` 标为 `failed` + `SERVER_RESTARTED`。
- 媒体文件随机名；原文件名只存元数据（脱敏显示）。

## 8. 数据流

> 以下流程图使用简写；完整路径、方法与状态码以 [API_CONTRACT.md](API_CONTRACT.md) 第 4 章为准（如 `/answers` 实为 `/v1/sessions/{id}/answers`，`/plan-jobs` 实为 `/v1/sessions/{id}/plan-jobs`）。

### 8.1 目标 → 计划

```text
目标/领域
  → POST /v1/sessions
  → 问题（按领域，最多两轮）
  → POST /answers
  → POST /plan-jobs（202）
  → 后台：提示词 + 参考资料 → DeepSeek JSON mode
  → Pydantic 校验（失败一次修复）
  → 保存 plan v1
  → 客户端轮询 Job → GET /plan
```

### 8.2 参考教程

```text
文字 → POST /references/text（同步）
文档/URL/图片/视频 → POST /references/import-*（202 Job）
  → 提取/校验/超限拒绝/警告（不截断）
  → Reference ready/failed
  → 生成计划时作为 <reference_material> 注入
```

### 8.3 媒体反馈

```text
选择照片/短片
  → POST /media（multipart）→ media_id
  → POST /feedback-jobs（media_ids）
  → ffprobe/Pillow/ffmpeg 抽帧
  → 多图 + 时间戳 + 条件/步骤 → DeepSeek
  → Pydantic 校验 Feedback（观察必须有证据）
  → 保存 feedback
  → 客户端轮询 → 展示证据/不确定性/限制
  → 可选 POST /revision-jobs → 审阅/应用
```

### 8.4 咖啡配方

```text
计划（coffee）→ POST /recipes（v1）
  → 用户 tasting（主观评分）
  → POST /adjustments（单变量、base_version）
  → 新配方版本 v2
  → GET /history、/compare（参数差异 + 用户评分差异）
```

### 8.5 Job 生命周期

```text
queued → running → succeeded/failed/cancelled
   └──────────────→ cancelled
终态结果保留 24h → expired
服务重启：queued/running → failed(SERVER_RESTARTED)
```

## 9. GitHub 版本管理

### 9.1 当前状态（2026-11-04）

- 项目目录**不是** Git 仓库；尚未初始化。
- `gh` 未安装；无 SSH key；无 GitHub token；GCM 二进制存在但无已存 GitHub 凭据；无 remote。
- GitHub 网络可达（`https://api.github.com/zen` 返回 200）。
- 结论：**当前不能直接推送**。可先做本地 Git；推送需要用户创建空仓库并提供 URL，或批准安装/登录 GitHub CLI，或由用户在终端完成 GCM 登录。

### 9.2 推荐流程

1. 用户在 GitHub 创建**私有**空仓库（建议名 `tutorial-coach`），不要勾选自动生成 README/.gitignore。
2. 用户提供 HTTPS URL（不要把 PAT 贴在聊天里）。
3. 本地：

```powershell
cd C:\Users\wwx\Documents\Codex\2026-11-04\w\outputs\tutorial-coach
git init -b main
git add .
git commit -m "docs: add tutorial-coach specification and delivery plan"
git remote add origin <用户提供的私有仓库URL>
git push -u origin main
```

4. 若 `git push` 需要登录：由用户在自己的终端运行（GCM 会打开浏览器）；或用户批准安装 GitHub CLI 后 `gh auth login`，再 `gh repo create`/`git push`。
5. 每个阶段结束提交并推送；标签：`v0.1.0-planning`、`v0.2.0-d1`……`v1.0.0-submission`。
6. 不强制推送 `main`；不在提交中放 `.env`、`local.properties`、keystore、APK、构建目录、个人媒体。
7. 私有仓库是默认；公开会泄露比赛材料/未完成内容，需用户明确同意。
8. 比赛源码包从标签导出；提交 commit hash 到 README/材料，便于复现。

### 9.3 不做什么

- 不自动安装 `gh`、不自动创建公开仓库、不读取/导出 GCM 凭据。
- 不把 Key 写入 remote URL（如 `https://token@github.com/...`）。
- 不提交 `server/data/`、`.venv/`、`android/build/`、`*.apk`、`*.jks`。

## 10. 成本与资源边界

- 不购买云服务、不发布商店、不引入付费组件。
- DeepSeek API 费用由用户账户承担；探针/演示控制 token；单次反馈最多 4 图或 8 帧。
- 不下载/打包模型权重；ffmpeg 为外部依赖。
- 本机磁盘：媒体/帧临时文件设置上限与清理；单视频 ≤100 MiB，抽帧临时目录处理完删除。
- 七天目标不保证；以每日闸门为准。

## 11. 环境验证清单（D1 必做）

| 检查 | 命令 | 通过标准 | 当前 |
|---|---|---|---|
| JDK 21 | `java -version`（会话 `JAVA_HOME` 指向 JBR） | 21.0.7 | 未验证构建 |
| Gradle | `.\gradlew.bat --version` | 8.9 + JVM 21 | 未验证 |
| SDK | `sdkmanager --list_installed` | platforms 35、build-tools 35/36 | 35 缺失 |
| 构建 | `.\gradlew.bat :app:assembleDebug` | BUILD SUCCESSFUL | 未验证 |
| 安装 | `adb install -r ...` | Success | 未验证：无设备/AVD |
| 启动 | `adb shell am start ...` | Activity 启动 | 未验证 |
| 服务端 | `uvicorn ...`；`/v1/health` | 200 + status ok/degraded（无 Key 为 degraded） | 未验证 |
| 模型文本 | 探针脚本 | 真实成功或明确 NO_KEY | 未验证：无 Key |
| 模型图片 | 探针脚本 | 真实成功或明确失败 | 未验证：无 Key |
| ffmpeg | `ffmpeg -version`；过滤器 | 7.0.2 + filters | 已验证存在 |
| GitHub | `git remote -v` | 有私有 remote 且 push 成功 | 未配置 |

## 12. 变更记录

| 日期 | 变更 |
|---|---|
| 2026-11-04 | 初版；主方案 AGP 8.7.3 + Gradle 8.9（已缓存）；修正无系统镜像/AVD、build-tools 35 缺失、JDK 25 不兼容；无 OpenCV；GitHub 推送受阻状态 |
