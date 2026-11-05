# D2 异常与恢复验证

> 失败路径用测试替身/httpx MockTransport/隔离 ASGI 应用验证；真实付费模型只用于成功计划与真机流程，二者不混写。

| 场景 | 测试/证据 | 结果 |
|---|---|---|
| 无 Key | `test_plan_job_without_key_fails_with_model_not_configured`；`test_missing_key_fails_without_calling_transport` | Job 失败 `MODEL_NOT_CONFIGURED` 503；不调用 transport |
| 限流 429 | `test_rate_limit_maps_retry_after`；`test_plan_job_surfaces_rate_limit_error` | `MODEL_RATE_LIMITED` 429，`retry_after_s=7/3`，retryable |
| 超时 | `test_timeout_maps_to_model_timeout`；`test_repair_timeout_is_propagated` | `MODEL_TIMEOUT` 504，retryable |
| 非法 JSON | `test_invalid_json_maps_to_bad_output_with_reason`；`test_invalid_json_then_valid_repair_succeeds`；`test_invalid_json_twice_fails_after_exactly_one_repair`；`test_two_invalid_json_http_responses_fail_job_with_retryable`（真实 ModelClient+MockTransport） | 首次非法 JSON 触发一次修复；两次非法 Job `MODEL_BAD_OUTPUT` + retryable=true；HTTP 调用数=2 |
| 限流等待 UI | `PlanViewModelTest.rateLimitBlocksGenerationAndRetryUntilWaitExpires`；`sessionChangeClearsOldRateLimitState` | 7 秒内 generate/retry 不新建 Job；等待结束可手动重试；切会话清理 |
| 模型拒绝 | `test_refusal_http_error_maps_to_model_refused`；`test_content_filter_finish_reason_maps_to_model_refused`；`test_model_refusal_is_not_repaired` | `MODEL_REFUSED` 422；不重试 |
| 结构校验失败 | `test_plan_example_rejects_invalid_phase_and_empty_criteria`；`test_two_invalid_drafts_fail_after_exactly_one_repair`；`test_plan_job_structural_failure_after_one_repair` | Pydantic 拒绝非法计划；一次修复后仍失败 → Job `MODEL_BAD_OUTPUT`；调用数=2 |
| Job 幂等/重放 | `test_plan_job_idempotency_replays_after_success`；`test_plan_job_idempotency_same_key_different_body_conflicts` | 相同 key/body 重放同一 202 Job；不同 body 409 `IDEMPOTENCY_CONFLICT` |
| 计划获取失败 | `PlanViewModelTest.successfulJobWithFailedPlanFetchRetriesOnlyTheFetch` | 第一次 GET 失败后只重试 GET；createCalls=1、loadCalls=2；最终 Ready |
| 旧会话不覆盖新会话 | 真机跨会话验证；`PlanViewModelTest`/Repository 守卫 | 新会话计划页无旧计划 |
| 修复次数 | 上述修复测试断言 | 最多一次修复；拒绝/超时不修复 |

证据：`server_pytest.log`（47 passed）、`android_test.log`、`android_test_results.txt`。