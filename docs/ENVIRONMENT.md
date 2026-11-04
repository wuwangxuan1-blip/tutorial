# 环境复测（P0/D1）

> 复测日期：2026-11-04。以下全部为本次会话真实命令输出摘要；未执行或受阻的项目明确标“未验证/BLOCKED”。不复制规划快照冒充复测。

## 1. 操作系统与 shell

| 项 | 实测 |
|---|---|
| OS | Windows 10.0.26200.0（Windows 11 Home China） |
| Shell | git-bash（Windows）/ PowerShell 5.1.26100.9711 |
| C 盘可用 | 约 124 GB |

## 2. Java / Gradle / AGP

| 检查 | 命令 | 真实结果 |
|---|---|---|
| 默认 Java | `java -version` | `java version "25.0.2"`；Gradle 8.9 不能用 JDK 25 运行 |
| JBR 21 | `D:/Java/ideaIU-2025.2.win/jbr/bin/java.exe -version` | `openjdk version "21.0.7"`（JBR-21.0.7+6-1038.58-jcef） |
| Gradle 版本 | `bash ./gradlew --version`（会话 JAVA_HOME=JBR21） | **PASS**：Gradle 8.9；Launcher JVM 21.0.7；见 `codearts_proof/day1/gradle_version.txt` |
| Gradle 缓存 | `ls ~/.gradle/wrapper/dists` | `gradle-8.9-bin`、`gradle-8.10.2-bin`、`gradle-9.2.1-bin` |
| AGP 缓存 | `ls ~/.gradle/caches/.../com.android.tools.build/gradle` | `8.5.0`、`8.7.3`、`9.0.0`（无 8.8.2） |
| Kotlin 插件缓存 | 同上 `org.jetbrains.kotlin/kotlin-gradle-plugin` | `2.0.0`、`2.0.20`、`2.0.21`、`2.2.10` |
| Compose BOM 缓存 | 同上 `androidx.compose/compose-bom` | `2024.05.00`、`2024.12.01` |

结论：会话级 `JAVA_HOME` 必须指向 JBR 21；项目 `gradle.properties` 同时设置 `org.gradle.java.home`。未修改系统变量。

## 3. Android SDK / 设备

| 项 | 真实结果 |
|---|---|
| SDK 根目录 | `C:\Users\wwx\AppData\Local\Android\Sdk` |
| platforms | `android-34`、`android-35` |
| build-tools | `34.0.0`、`36.0.0`；**35.0.0 缺失** |
| platform-tools | adb 1.0.41 / 37.0.0 |
| emulator | 36.6.11 |
| `adb devices -l` | 空列表，无设备（`codearts_proof/day1/device_status.txt`） |
| `emulator -list-avds` | 无输出，无 AVD |
| system-images | `android-34/google_apis/x86_64` 仅有 `.installer` 残留，不是可用镜像 |
| sdkmanager | `--list_installed` 可运行；有 “only understands SDK XML versions up to 3 but ... version 4” 警告 |

结论：工程配置 build-tools 36.0.0；设备安装/启动 BLOCKED。

## 4. Python / 服务端依赖

| 项 | 真实结果 |
|---|---|
| Python | 3.12.9（`D:\Users\wwx\miniconda3\python.exe`） |
| 项目 venv | `server/.venv`，pip 24.3.1 |
| 已安装 | fastapi 0.162.0、uvicorn 0.54.0、httpx 0.28.1、pydantic 2.14.2、python-dotenv 1.2.4、pytest 8.4.2、pytest-asyncio 0.25.3 |
| 锁文件 | `server/requirements.txt`（pip freeze） |
| 服务端测试 | `pytest -v`：**21 项 PASS**；见 `codearts_proof/day1/server_pytest.log` |

## 5. ffmpeg

| 检查 | 真实结果 |
|---|---|
| `ffmpeg -version` | ffmpeg 7.0.2-full_build-www.gyan.dev |
| `ffprobe -version` | ffprobe 7.0.2-full_build-www.gyan.dev |
| 构建配置 | 含 `--enable-libvidstab`、`--enable-libvmaf` |

## 6. DeepSeek 配置与真实探针

| 项 | 结果 |
|---|---|
| `server/.env` 存在 | 是 |
| 键名 | `DEEPSEEK_BASE_URL`、`DEEPSEEK_API_KEY`、`DEEPSEEK_TEXT_MODEL`、`DEEPSEEK_VISION_MODEL` |
| Key 是否非空 | 是（只检查存在性，不输出值） |
| 模型列表 | HTTP 200；可用 `deepseek-flash`、`deepseek-v4-pro` |
| 文本探针 | **PASS**：`deepseek-flash`，约 1.3 s，输出“收到” |
| JSON 探针 | **PASS**：返回 `{"status":"ok","value":42}`，可解析 |
| 图片探针 | **PASS**：本地生成 64x64 橙色 PNG，模型回答“橙色” |
| 证据 | `codearts_proof/day1/model_probe.json`（已脱敏） |

补充实测：
- 单次调用“推理 + 输出”超过 8192 token 会被截断（`finish_reason=length`）；计划提示词已收敛到 3–5 步并通过。
- 该推理模型可能把内容放在 `reasoning_content`、`content` 为空；代码已识别并返回明确 `MODEL_BAD_OUTPUT`，不当作成功。

## 7. 最小垂直流程（服务端真实调用）

| 项 | 结果 |
|---|---|
| 目标 | “2 人份番茄鸡蛋面，30 分钟内完成” |
| 会话 | 创建后 `clarifying`，返回 5 个烹饪问题 |
| 回答 | 一轮回答后 `ready` |
| 计划 Job | 202 → succeeded |
| 真实模型计划 | 4 步；有假设、完成标准、安全提示 |
| 证据 | `codearts_proof/day1/vertical_flow.json`、`vertical_flow.log`、`session_create.json`、`health.json` |

说明：沙箱禁止本地回环连接，Web 流程使用 `httpx.ASGITransport` 驱动同一 FastAPI 应用；模型调用是真实外网请求，不是替身。Android 设备端步骤卡因无设备未验证。

## 8. Git / GitHub

| 项 | 真实结果 |
|---|---|
| 仓库 | 已有 `.git`；分支 `main` 跟踪 `origin/main` |
| remote | `https://github.com/wuwangxuan1-blip/tutorial.git` |
| 基线 | `ab6996a docs: add Android practice coach specifications and development plan` |
| P0 提交 | `bcd3cc9 feat: implement D1 P0 vertical slice with real model probes` |
| 状态文档提交 | `4798f2f docs: record D1 git push and verification status` |
| 只读远程测试 | 早期 `git ls-remote` 被沙箱拦截；推送后执行 `git ls-remote --heads origin main` 返回 `bcd3cc9... refs/heads/main` |
| 推送 | **PASS**：`git push origin main` 成功（`ab6996a..bcd3cc9 main -> main`），未强推 |
| 本地/远程一致性 | `git status -sb` 显示 `## main...origin/main`；远程 main 指向 `bcd3cc9` |

## 9. 构建与安装状态

| 项 | 状态 |
|---|---|
| `gradlew --version` | PASS（Gradle 8.9 + JVM 21.0.7） |
| `:app:assembleDebug` | Codex 复审环境 2026-11-04T15:58Z：`BUILD SUCCESSFUL in 27s`；码道本会话沙箱无法执行该任务（命令被拦截、无日志）。最终源码在 P2 修复后尚未重建 |
| APK | 已生成 `android/app/build/outputs/apk/debug/app-debug.apk`（约 10 MB，`aapt2` 核验包名/版本/SDK）；但构建早于 P2 修复，需重建 |
| 设备安装/启动/截图 | BLOCKED（无设备/AVD/镜像） |
| Android JVM 测试 | Codex 构建时 11 项 PASS；新增 `PlanViewModelTest` 后尚未复跑 |
| FastAPI `/v1/health` | PASS：200、`status=ok`、无 Key |
| 模型探针 | PASS：文本/JSON/图片 |
| 真实计划垂直流程 | PASS（服务端）；Android UI 未设备验证 |

## 10. 证据与秘密

- `codearts_proof/day1/secret_scan.json`：扫描工作区文本文件，未发现真实 Key/Key 模式；`clean=true`。
- `.env` 被 `.gitignore` 排除；不提交。
- 运行数据 `server/data/` 已被忽略；证据只保留脱敏副本。