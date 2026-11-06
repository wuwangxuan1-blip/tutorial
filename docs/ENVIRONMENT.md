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
| Gradle 版本 | `bash ./gradlew --version`（标准 Wrapper，会话 JAVA_HOME=JBR21） | **PASS**：Gradle 8.9；Launcher JVM 21.0.7；见 `codearts_proof/day1/gradle_version.txt` |
| Wrapper | `android/gradle/wrapper/gradle-wrapper.properties` | 官方 `https://services.gradle.org/distributions/gradle-8.9-bin.zip`；SHA-256 `d725d707...cecab`；标准 jar/脚本已生成 |
| Gradle 缓存 | `ls ~/.gradle/wrapper/dists` | `gradle-8.9-bin`、`gradle-8.10.2-bin`、`gradle-9.2.1-bin` |
| AGP 缓存 | `ls ~/.gradle/caches/.../com.android.tools.build/gradle` | `8.5.0`、`8.7.3`、`9.0.0`（无 8.8.2） |
| Kotlin 插件缓存 | 同上 `org.jetbrains.kotlin/kotlin-gradle-plugin` | `2.0.0`、`2.0.20`、`2.0.21`、`2.2.10` |
| Compose BOM 缓存 | 同上 `androidx.compose/compose-bom` | `2024.05.00`、`2024.12.01` |

结论：会话级 `JAVA_HOME` 必须指向 JDK 21（本机 JBR 21.0.7）；`android/gradle.properties` 已移除个人 JDK 绝对路径，不再设置 `org.gradle.java.home`。未修改系统变量。

## 3. Android SDK / 设备

| 项 | 真实结果 |
|---|---|
| SDK 根目录 | `C:\Users\wwx\AppData\Local\Android\Sdk` |
| platforms | `android-34`、`android-35` |
| build-tools | `34.0.0`、`36.0.0`；**35.0.0 缺失** |
| platform-tools | adb 1.0.41 / 37.0.0 |
| emulator | 36.6.11 |
| `adb devices -l` | `eeffd16b device`（realme GT6 / RMX3800，Android 16）；见 `device_verification.md` |
| `emulator -list-avds` | 无输出，无 AVD |
| system-images | `android-34/google_apis/x86_64` 仅有 `.installer` 残留，不是可用镜像 |
| sdkmanager | `--list_installed` 可运行；有 “only understands SDK XML versions up to 3 but ... version 4” 警告 |

结论：工程配置 build-tools 36.0.0；真机已连接并完成安装、启动与最小垂直流程验证；无 AVD。

## 4. Python / 服务端依赖

| 项 | 真实结果 |
|---|---|
| Python | 3.12.9（`D:\Users\wwx\miniconda3\python.exe`） |
| 项目 venv | `server/.venv`，pip 24.3.1 |
| 已安装 | fastapi 0.162.0、uvicorn 0.54.0、httpx 0.28.1、pydantic 2.14.2、python-dotenv 1.2.4、pytest 8.4.2、pytest-asyncio 0.25.3 |
| 锁文件 | `server/requirements.txt`（pip freeze） |
| 服务端测试 | `pytest -v`（P1 复审后）：**47 项 PASS**；见 `codearts_proof/day2/server_pytest.log` |

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
| 第三轮修复提交 | `f405461 fix(android): fix P0 regression test and restore standard Gradle wrapper` |
| 真机验证提交 | `8a6365d docs: add P0 real-device verification evidence` |
| D2 提交 | `e268dfe feat: complete D2 contract and cooking text flow` |
| P1 复审修复提交 | `741b2e4 fix: handle rate limit wait and generic allergy assumptions` |
| 推送 | **PASS**：`ab6996a..bcd3cc9`、`bcd3cc9..4798f2f`、`4798f2f..f405461`、`2c168db..8a6365d`、`8c5054d..e268dfe`、`2d232e2..741b2e4`；未强推 |
| 本地/远程一致性 | 推送后 `git status -sb` 显示 `## main...origin/main`；远程 main 指向 `741b2e4`（随后仅文档提交） |

## 9. 构建与安装状态

| 项 | 状态 |
|---|---|
| `gradlew --version` | PASS（Gradle 8.9 + JVM 21.0.7） |
| `:app:assembleDebug` | **PASS**：标准 Wrapper + JBR 21，`:app:assembleDebug --rerun-tasks` `BUILD SUCCESSFUL in 28s`（35 任务全部执行）；见 `android_build_round3.log` |
| APK | `android/app/build/outputs/apk/debug/app-debug.apk`（D2 约 11 MB，2026-11-05 13:21）；`aapt2` 核验包名/版本/SDK 通过 |
| 设备安装/启动/截图 | **PASS（最小流程）**：`adb install -r` Success；冷启动成功；首页/澄清/真实计划/步骤卡/诊断页均验证；截图保存在本地未提交 |
| 断网恢复 | **PASS**：停止服务端→首页“服务端：未连接”；重启→“服务端：正常” |
| 真机跨会话隔离 | **PASS**：第二个会话计划页无上一会话计划残留 |
| 未真机验证项 | 旋转、切后台、进程被杀恢复；中文目标输入；第二份计划真实生成 |
| Android JVM 测试 | **PASS（P1 复审后）**：21 项，0 失败；含 ContractExamplesTest 6、ErrorMapper 5、PlanViewModel 3；见 `codearts_proof/day2/android_test_results.txt` |
| FastAPI `/v1/health` | PASS：200、`status=ok`、无 Key |
| 模型探针 | PASS：文本/JSON/图片 |
| 真实计划垂直流程 | PASS（服务端 + 真机 UI：5 步计划、步骤卡） |
| 真机模型调用 | PASS：26.449 s / 4445 tokens（`device_server_full.log`） |

## 10. 证据与秘密

- `codearts_proof/day1/secret_scan.json`：扫描工作区文本文件，未发现真实 Key/Key 模式；`clean=true`。
- `codearts_proof/day1/device_verification.md`：真机安装、主流程、诊断、跨会话、断网恢复脱敏摘要。
- 截图 `device_home.png`、`device_step.png` 仅在本地，未提交；无个人媒体入库。
- `.env` 被 `.gitignore` 排除；不提交。
- 运行数据 `server/data/` 已被忽略；证据只保留脱敏副本。
## 11. P1/D2 阶段补充（2026-11-05）

| 项 | 实测 |
|---|---|
| 契约样例 | `contracts/examples/` 7 个 JSON；服务端 `test_contract_examples.py` 8 项、安卓 `ContractExamplesTest` 6 项通过 |
| 服务端测试 | 47 项通过（含模型错误、修复重试、两轮澄清、Job 失败/幂等、真实 ModelClient+MockTransport 非法 JSON） |
| 安卓测试 | 21 项通过（0 失败；含限流等待与切会话清理） |
| APK | 本轮构建约 11 MB；`com.tutorialcoach.app` / 0.1.0 / minSdk 26 / targetSdk 35 |
| 真实模型流程 | 中文目标“两人份番茄鸡蛋面，30 分钟内完成”：两轮澄清→5 步计划；30.837 s / 5196 tokens；8 条假设；`stage=done` |
| 真机 D2 | 真机完成两轮澄清、计划页（含 6 条假设、准备清单、安全提示）、步骤卡 1/5→2/5；设备端目标用 ASCII（adb 限制），模型输出中文 |
| 真机模型调用 | 27.079 s / 4682 tokens（最新计划；`day2/device_server_full.log`） |
| `gradlew` 模式 | `git ls-files -s android/gradlew` = `100755` |
| 未覆盖 | 旋转/切后台/进程恢复、中文输入法、视觉截图检查、干净机器首次 Gradle/Maven 下载 |

## 12. P1 复审三项修复（2026-11-05）

| 项 | 实测 |
|---|---|
| 服务端测试 | **47 passed**（新增真实 ModelClient+MockTransport 两次非法 JSON、蘑菇汤过敏提示、明确无过敏） |
| 安卓测试 | **21 passed**（新增 PlanViewModel 限流等待 7 秒与切会话清理） |
| APK | 修复后构建成功，约 11 MB |
| 限流等待 | JVM 假网关验证：等待期间 generate/retry 不新建 Job；7 秒后可手动重试；切会话清理；未真机注入 429 |
| 非法 JSON | 真实 ModelClient + httpx.MockTransport 两次非法：Job `MODEL_BAD_OUTPUT`、retryable=true、调用数=2；无真实模型调用 |
| 过敏提示 | 未提供时通用提示；`allergies=[]` 不提示；蘑菇汤假计划测试通过；真实番茄鸡蛋面流程重跑 5 步/8 假设/30.837 s/5196 tokens |
| 未覆盖 | 真机未重跑限流 UI/过敏提示；设备 D2 记录仍为上一版提示，已在 `day2/device_verification.md` 标注 |


## 13. D4 环境与媒体能力（2026-11-05）

| 项 | 实测 |
|---|---|
| Python 媒体依赖 | 已安装并锁定 `pillow==13.0.0`、`python-multipart==0.0.33` |
| FFmpeg | `ffmpeg`/`ffprobe` 可用；`vidstabdetect` ASCII + `vidstabtransform(debug=1)` 的 `global_motions.trf` 可解析；合成 8 秒视频 frame_count=80 |
| 真实视觉探针 | 文本/JSON/视觉均 ok；64×64 橙色 PNG 返回“橙色”；`day4/vision_probe.json` |
| 真实视觉 + 合成素材反馈 | 图片与 8 秒视频两次 feedback Job 均 succeeded；视频时间戳 0–7s、motion_metrics 非空、audio_analyzed=false；均评估 not_verified 并明确指出合成素材 |
| 服务端测试 | **88 passed**（新增 media 4 / feedback 5 / photography 3） |
| Android 测试 | **41 passed**（新增 MediaLimits 2 / MediaViewModel 2） |
| APK | `android/app/build/outputs/apk/debug/app-debug.apk`，10,783,309 字节 |
| 真实图片/短片反馈 | **BLOCKED**：缺用户真实拍摄素材；未用截图或合成素材冒充真实拍摄 |
| 未覆盖 | 设备端 Photo Picker/上传/反馈页未走查；真实素材反馈、HEIC 在 API 26/27 的转换未验证 |
## 14. D4 复审修复实测（2026-11-05）

| 项 | 实测 |
|---|---|
| 服务端测试 | **90 passed**（D4 基线 88 + 反馈会话锁/版本冲突 2 项） |
| Android 测试 | **43 tests / 0 failures**（`MediaViewModelTest` 4 项；新增视频证据帧时间戳与缺失不回退 2 项） |
| APK | `android/app/build/outputs/apk/debug/app-debug.apk`，10,798,800 字节（复审修复后重构建） |
| `git diff --check` | 通过（exit 0） |
| 密钥扫描 | 262 文件、0 匹配、`clean=true` |
| 真实素材 | 仍 **BLOCKED**：真机技术走查使用界面截图，不是咖啡拍摄；真实图片/短片反馈未验收 |
| 未覆盖 | 真机视频证据帧 UI 未复测（JVM 覆盖提取映射与无回退）；Canvas/配方属 D5 |

## 15. D4 剩余 P2 证据帧实测（2026-11-05）

| 项 | 实测 |
|---|---|
| 服务端测试 | **91 passed**（上一轮 90 + 证据帧与模型输入字节一致 1 项） |
| Android 测试 | **43 tests / 0 failures**（视频证据帧改为下载服务端保存的模型输入帧） |
| APK | `android/app/build/outputs/apk/debug/app-debug.apk`，10,816,510 字节 |
| 契约 | `docs/API_CONTRACT.md` 3.7/4.4 新增证据帧端点与客户端约束 |
| `git diff --check` | 通过（exit 0） |
| 密钥扫描 | 263 文件、0 匹配、`clean=true` |
| 真实素材 | 仍 **BLOCKED**；合成短片只用于技术测试 |
| 未覆盖 | 真机视频证据帧 UI 未复测；Canvas/配方属 D5 |
## 16. D5 摄影运镜与咖啡配方实测（2026-11-05）

| 项 | 实测 |
|---|---|
| 服务端测试 | **108 passed / 0 failed**（D5 新增 camera 14、recipe 2、摄影计划 1） |
| Android 测试 | **52 tests / 0 failures**（CameraMoveValidator 3、CameraPlayback 1、RecipeViewModel 3、Dto +2） |
| APK | `android/app/build/outputs/apk/debug/app-debug.apk`，10,869,987 字节 |
| 真实模型 | 摄影计划含合法 `orbit_cw`（8 秒）；V60 计划含 15 g / 225 g / 92 °C / 150 秒；证据帧字节一致的 D4 回归保留 |
| 真机 | RMX3800 / Android 16 / `eeffd16b`；运镜播放/暂停/重播通过；咖啡 v1 + 品尝表单通过；口味保存/调整/对比 **BLOCKED**（工具权限拒绝） |
| 未覆盖 | 真机配方单变量调整与对比；设备截图 AI 视觉检查 |
### D5 补验实测（2026-11-05）

| 项 | 实测 |
|---|---|
| 第三方实拍 | CC0 照片反馈 `unclear`；CC BY-SA 4.0 短片主反馈 `unclear`，4/4 帧字节一致；倒咖啡反例 `not_met`，5/5 帧字节一致 |
| D4 状态 | 第三方实拍链路通过；用户自拍环绕仍 BLOCKED |
| 运镜 | 新增拖动时间轴 `seek()`；JVM 覆盖，真机新 APK 已装但拖动未再次走查 |
| 咖啡 | 真实模型 92→90 v2/compare 实际通过；真机 v1+用户评分保存成功，真机调整/对比/断网重试 BLOCKED |
| 测试/构建 | 服务端 108 passed；Android 52 tests / 0 failures；`assembleDebug` 成功；APK 10,869,987 字节 |
### D5 复审三项修复实测（2026-11-05）

| 项 | 实测 |
|---|---|
| 服务端测试 | **111 passed / 0 failed**（配方测试 5 项：计划参数/demo、225→240 派生、92→90、多变量/冲突/失败不写） |
| Android 测试 | **55 tests / 0 failures**（CameraEasing 2、RecipeViewModel 4） |
| APK | `android/app/build/outputs/apk/debug/app-debug.apk`，10,896,532 字节 |
| 真实模型 | 非 demo 路径从计划解析 15/225/15/92/150，用户测试 tasting → 92→90 v2/compare |
| 状态 | 第三方实拍通过；用户自拍环绕 BLOCKED；真机配方对比 BLOCKED；断网重试 BLOCKED；真机 easing/拖动未复测 |
### D5 配方复审再修实测（2026-11-06）

| 项 | 实测 |
|---|---|
| 服务端测试 | **114 passed / 0 failed**（配方测试 8 项：语义化步骤/同值变量、中文时长、先校验后派生均覆盖） |
| Android 测试 | **55 tests / 0 failures** |
| APK | `android/app/build/outputs/apk/debug/app-debug.apk`，10,822,322 字节 |
| 真实模型 | V60 计划解析 15/225/15/92/150 → 92→90 v2/compare 通过 |
| 状态 | 第三方实拍通过；用户自拍环绕 BLOCKED；真机配方对比 BLOCKED；断网重试 BLOCKED |
### D5 配方复审收尾实测（2026-11-06）

| 项 | 实测 |
|---|---|
| 服务端测试 | **116 passed / 0 failed**（配方测试 10 项：总水量歧义、闷蒸 vs 总水量、总时长优先、中文分钟步骤改写均覆盖） |
| Android 测试 | **55 tests / 0 failures** |
| APK | `android/app/build/outputs/apk/debug/app-debug.apk`，10,822,322 字节 |
| 真实模型 | V60 计划解析总水量 225、ratio 1:15；92→90 v2/compare 通过 |
| 状态 | 第三方实拍通过；用户自拍环绕 BLOCKED；真机配方对比 BLOCKED；断网重试 BLOCKED |
### D5 配方解析优先级修复实测（2026-11-06）

| 项 | 实测 |
|---|---|
| 服务端测试 | **120 passed / 0 failed**（配方 14 项：显式总水量优先、无总量仅唯一终值、多阶段/局部 422、中英文冒号总时长优先、只改显式总时长） |
| Android 测试 | **55 tests / 0 failures**（本轮未改 Android） |
| APK | `android/app/build/outputs/apk/debug/app-debug.apk`，10,822,322 字节 |
| 状态 | 第三方实拍通过；用户自拍环绕 BLOCKED；真机配方对比 BLOCKED；断网重试 BLOCKED |
### D5 配方创建/调整总量一致性实测（2026-11-06）

| 项 | 实测 |
|---|---|
| 服务端测试 | **122 passed / 0 failed**（配方 16 项：注水总量按位置改写、静置时长不改、旧值保留、总量优先/歧义 422） |
| Android 测试 | **55 tests / 0 failures**（本轮未改 Android） |
| APK | `android/app/build/outputs/apk/debug/app-debug.apk`，10,822,322 字节 |
| 状态 | 第三方实拍通过；用户自拍环绕 BLOCKED；真机配方对比 BLOCKED；断网重试 BLOCKED |
