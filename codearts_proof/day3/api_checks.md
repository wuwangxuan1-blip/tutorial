# D3 服务端行为检查

## PLAN_LOCKED

会话 `sess_01M6NG28XPBB3SFPE71DM6ZJDQ` 已有 `step_1=done`、`step_2=in_progress`、计划版本 2。

```text
POST /v1/sessions/sess_01M6NG28XPBB3SFPE71DM6ZJDQ/plan-jobs
{"base_plan_version":2}
→ HTTP 409
{"error":{"code":"PLAN_LOCKED","message":"已有步骤进度，不能全量重新生成；请使用条件修订或新建会话。","retryable":false,"retry_after_s":null,"details":{}}}
```

## 修订应用保留已完成步骤

对比同会话计划 v1 与 v2：

```text
v1 step1 == v2 step1: True
v2 step1 title: 备份源照片并确认可读
```

修订只更新 `step_2/step_3/step_4`；`step_1` 的内容、`done` 状态与 `self_reported` 证据保持不变。

## 修订状态

```text
rev_01M6NHWW00H7FC880NYTAXJ4P7 applied 1
rev_01M6NHZ9KJV3N3GFF0GZ7PTQJQ rejected 2
```

## 条件 PATCH

- `changed_fields=["notes"]`
- `requires_revision=true`（已有进度）
- 条件 PATCH 的省略/null/空串/关键字段 null 由 `server/tests/test_conditions.py` 覆盖。