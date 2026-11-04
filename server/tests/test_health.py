from __future__ import annotations


async def test_health_returns_degraded_without_key(client):
    response = await client.get("/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["api_version"] == "v1"
    assert body["status"] == "degraded"
    assert body["checks"]["store"] is True
    assert body["checks"]["model_configured"] is False
    assert "sk-" not in response.text
    assert "DEEPSEEK_API_KEY" not in response.text


async def test_capabilities_lists_domains_and_limits(client):
    response = await client.get("/v1/capabilities")
    assert response.status_code == 200
    body = response.json()
    assert body["domains"] == ["cooking", "photography", "software", "coffee"]
    assert body["model"]["configured"] is False
    assert body["model"]["vision_supported"] is None
    assert body["model"]["audio_analysis"] is False
    assert body["limits"]["plan_steps_max"] == 15
    assert body["limits"]["reference_total_max_chars"] == 20000


async def test_unknown_route_uses_error_envelope(client):
    response = await client.get("/v1/unknown")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "NOT_FOUND"
    assert body["error"]["request_id"].startswith("req_")
    assert response.headers["X-Request-Id"] == body["error"]["request_id"]