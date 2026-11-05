# D4 实际命令（摘录）

## 服务端

```text
cd server
.venv/Scripts/python.exe -m pip install pillow python-multipart
.venv/Scripts/python.exe -m pytest -o addopts=""
→ 88 passed
```

## 视觉探针（真实 DeepSeek）

```text
server/.venv/Scripts/python.exe scripts/probe_deepseek.py \
  --output codearts_proof/day4/vision_probe.json \
  --data-copy server/data/model_probe.json
→ {"text":"ok","json":"ok","image":"ok"}
→ 橙色
```

## Android

```powershell
$env:JAVA_HOME='D:\Java\ideaIU-2025.2.win\jbr'
cd android
.\gradlew.bat --no-daemon --console=plain :app:testDebugUnitTest
→ BUILD SUCCESSFUL；41 tests
.\gradlew.bat --no-daemon --console=plain :app:assembleDebug
→ BUILD SUCCESSFUL
```

## 真实摄影计划 + 真实视觉技术反馈（合成素材）

服务端 `127.0.0.1:8000`，真实 DeepSeek：

- 创建摄影会话：`sess_01M6NXX22MQQD2K2CEBKZT1QDQ`
- 真实计划：`手机竖屏手持环绕拍一杯咖啡 8 秒`，5 步，v1，`visual_aid=null`
- 上传合成 PNG 咖啡杯示意图 + 8 秒合成 testsrc MP4
- 两次 feedback-jobs 均 succeeded；图片评估 `not_verified`、视频评估 `not_verified`
- 视频回包 sampled timestamps `[0,1,2,3,4,5,6,7]`，motion_metrics 非空，audio_analyzed=false
- 证据：`plan_photography_real.json`、`technical_synthetic_feedback.json`

说明：合成素材仅用于技术验证，不是真实拍摄；真实图片/短片反馈 BLOCKED。