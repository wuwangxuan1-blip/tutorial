from __future__ import annotations

import asyncio

from app.errors import ApiError
from app.services import feedback_service as feedback_module
from test_media import image_bytes, upload, video_bytes
from test_progress import setup_plan, wait_job


def fake_vision(
    media_id: str,
    *,
    kind: str = "image",
    frame_index=None,
    timestamp_s=None,
    assessment: str = "likely_met",
    evidence_override=None,
):
    async def fake(
        system_prompt,
        user_prompt,
        model=None,
        timeout_s=None,
        vision_images=None,
    ):
        evidence = evidence_override
        if evidence is None:
            evidence = {
                "media_id": media_id,
                "kind": kind,
                "frame_index": frame_index,
                "timestamp_s": timestamp_s,
            }
        return {
            "summary": "可见画面给出定性观察。",
            "observations": [
                {
                    "text": "主体在画面内，细节可辨认。",
                    "evidence": evidence,
                    "certainty": "medium",
                }
            ],
            "assessment": assessment,
            "uncertainties": ["未看到完整的拍摄环境。"],
            "limitations": ["单帧只能做定性观察。"],
            "suggested_actions": ["保持主体在画面中央。"],
            "follow_up_questions": ["还有没有其他角度的照片？"],
        }

    return fake


async def test_image_feedback_has_evidence_and_does_not_complete_step(client, monkeypatch):
    session, _ = await setup_plan(client, monkeypatch)
    media = (await upload(client, image_bytes(), "image/jpeg", "photo.jpg", "image")).json()
    fake = fake_vision(media["id"])

    async def fake_chat(
        system_prompt,
        user_prompt,
        model=None,
        timeout_s=None,
        vision_images=None,
    ):
        assert vision_images and len(vision_images) == 1
        return await fake(system_prompt, user_prompt, model, timeout_s, vision_images)

    monkeypatch.setattr(client.app.state.model_client, "chat_json", fake_chat)
    response = await client.post(
        f"/v1/sessions/{session['id']}/feedback-jobs",
        json={
            "step_id": "step_1",
            "plan_version": 1,
            "media_ids": [media["id"]],
            "note": "看看备料。",
        },
    )
    assert response.status_code == 202, response.text
    job = await wait_job(client, response.json()["id"])
    assert job["status"] == "succeeded", job
    feedback_id = job["result"]["feedback_id"]

    feedback = (await client.get(f"/v1/feedback/{feedback_id}")).json()
    analysis = feedback["analysis"]
    assert analysis["observations"][0]["evidence"]["media_id"] == media["id"]
    assert analysis["observations"][0]["evidence"]["kind"] == "image"
    assert analysis["observations"][0]["evidence"]["frame_index"] is None
    assert analysis["audio_analyzed"] is False
    assert "不分析音频" in analysis["audio_note"]
    assert analysis["motion_metrics"] is None
    assert analysis["sampled_frame_timestamps_s"] == []
    assert any("内部温度" in item for item in analysis["limitations"])
    assert any("口味" in item for item in analysis["limitations"])

    fresh = (await client.get(f"/v1/sessions/{session['id']}")).json()
    assert fresh["progress"]["step_statuses"] == {}
    assert fresh["progress"]["evidence_levels"]["step_1"] == "model_observed"

    listing = await client.get(f"/v1/sessions/{session['id']}/feedback")
    assert listing.status_code == 200
    assert listing.json()["items"][0]["id"] == feedback_id


async def test_feedback_rejects_missing_or_wrong_evidence(client, monkeypatch):
    session, _ = await setup_plan(client, monkeypatch)
    media = (await upload(client, image_bytes(), "image/jpeg", "photo.jpg", "image")).json()

    missing = fake_vision(media["id"], evidence_override={})
    monkeypatch.setattr(client.app.state.model_client, "chat_json", missing)
    response = await client.post(
        f"/v1/sessions/{session['id']}/feedback-jobs",
        json={"step_id": "step_1", "plan_version": 1, "media_ids": [media["id"]]},
    )
    job = await wait_job(client, response.json()["id"])
    assert job["status"] == "failed"
    assert job["error"]["error"]["code"] == "MODEL_BAD_OUTPUT"
    assert (await client.get(f"/v1/sessions/{session['id']}/feedback")).json()["items"] == []

    wrong = fake_vision("media_not_submitted")
    monkeypatch.setattr(client.app.state.model_client, "chat_json", wrong)
    response = await client.post(
        f"/v1/sessions/{session['id']}/feedback-jobs",
        json={"step_id": "step_1", "plan_version": 1, "media_ids": [media["id"]]},
    )
    job = await wait_job(client, response.json()["id"])
    assert job["status"] == "failed"
    assert job["error"]["error"]["details"]["reason"] == "evidence_media_mismatch"

    image_with_frame = fake_vision(media["id"], frame_index=0, timestamp_s=0.0)
    monkeypatch.setattr(client.app.state.model_client, "chat_json", image_with_frame)
    response = await client.post(
        f"/v1/sessions/{session['id']}/feedback-jobs",
        json={"step_id": "step_1", "plan_version": 1, "media_ids": [media["id"]]},
    )
    job = await wait_job(client, response.json()["id"])
    assert job["status"] == "failed"
    assert job["error"]["error"]["details"]["reason"] == "feedback_validation_failed"


async def test_video_feedback_timestamps_motion_and_audio_false(client, monkeypatch):
    session, _ = await setup_plan(client, monkeypatch)
    video = (await upload(client, video_bytes(2), "video/mp4", "clip.mp4", "video")).json()
    fake = fake_vision(
        video["id"],
        kind="video_frame",
        frame_index=0,
        timestamp_s=0.0,
        assessment="unclear",
    )
    monkeypatch.setattr(client.app.state.model_client, "chat_json", fake)

    response = await client.post(
        f"/v1/sessions/{session['id']}/feedback-jobs",
        json={"step_id": "step_1", "plan_version": 1, "media_ids": [video["id"]]},
    )
    job = await wait_job(client, response.json()["id"])
    assert job["status"] == "succeeded", job
    feedback = (await client.get(f"/v1/feedback/{job['result']['feedback_id']}")).json()
    analysis = feedback["analysis"]
    assert analysis["sampled_frame_timestamps_s"] == [0.0, 1.0]
    assert analysis["audio_analyzed"] is False
    assert analysis["observations"][0]["evidence"]["kind"] == "video_frame"
    assert analysis["motion_metrics"] is not None
    assert analysis["motion_metrics"]["method"] == "vidstabdetect_ascii_10fps_320px+global_motions"
    assert analysis["motion_metrics"]["frame_count"] >= 2


async def test_video_feedback_rejects_bad_timestamp_and_motion_failure(client, monkeypatch):
    session, _ = await setup_plan(client, monkeypatch)
    video = (await upload(client, video_bytes(2), "video/mp4", "clip.mp4", "video")).json()

    bad = fake_vision(
        video["id"],
        kind="video_frame",
        frame_index=0,
        timestamp_s=5.0,
    )
    monkeypatch.setattr(client.app.state.model_client, "chat_json", bad)
    response = await client.post(
        f"/v1/sessions/{session['id']}/feedback-jobs",
        json={"step_id": "step_1", "plan_version": 1, "media_ids": [video["id"]]},
    )
    job = await wait_job(client, response.json()["id"])
    assert job["status"] == "failed"
    assert job["error"]["error"]["details"]["reason"] == "evidence_timestamp_mismatch"

    async def no_motion(path, temp_dir):
        return None

    monkeypatch.setattr(feedback_module, "motion_metrics", no_motion)
    good = fake_vision(
        video["id"],
        kind="video_frame",
        frame_index=0,
        timestamp_s=0.0,
        assessment="unclear",
    )
    monkeypatch.setattr(client.app.state.model_client, "chat_json", good)
    response = await client.post(
        f"/v1/sessions/{session['id']}/feedback-jobs",
        json={"step_id": "step_1", "plan_version": 1, "media_ids": [video["id"]]},
    )
    job = await wait_job(client, response.json()["id"])
    assert job["status"] == "succeeded", job
    feedback = (await client.get(f"/v1/feedback/{job['result']['feedback_id']}")).json()
    analysis = feedback["analysis"]
    assert analysis["motion_metrics"] is None
    assert any("未启用运动估计" in item for item in analysis["limitations"])


async def test_feedback_request_validation_and_vision_unsupported(client, monkeypatch):
    session, _ = await setup_plan(client, monkeypatch)
    image = (await upload(client, image_bytes(), "image/jpeg", "photo.jpg", "image")).json()
    video = (await upload(client, video_bytes(1), "video/mp4", "clip.mp4", "video")).json()

    mixed = await client.post(
        f"/v1/sessions/{session['id']}/feedback-jobs",
        json={"step_id": "step_1", "plan_version": 1, "media_ids": [image["id"], video["id"]]},
    )
    assert mixed.status_code == 422
    assert mixed.json()["error"]["details"]["reason"] == "mixed_media"

    too_many = await client.post(
        f"/v1/sessions/{session['id']}/feedback-jobs",
        json={
            "step_id": "step_1",
            "plan_version": 1,
            "media_ids": [f"media_{index}" for index in range(5)],
        },
    )
    assert too_many.status_code == 422

    conflict = await client.post(
        f"/v1/sessions/{session['id']}/feedback-jobs",
        json={"step_id": "step_1", "plan_version": 9, "media_ids": [image["id"]]},
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"]["code"] == "VERSION_CONFLICT"

    async def unsupported(
        system_prompt,
        user_prompt,
        model=None,
        timeout_s=None,
        vision_images=None,
    ):
        raise ApiError(503, "VISION_UNSUPPORTED", "当前模型端点不支持图片输入。")

    monkeypatch.setattr(client.app.state.model_client, "chat_json", unsupported)
    response = await client.post(
        f"/v1/sessions/{session['id']}/feedback-jobs",
        json={"step_id": "step_1", "plan_version": 1, "media_ids": [image["id"]]},
    )
    job = await wait_job(client, response.json()["id"])
    assert job["status"] == "failed"
    assert job["error"]["error"]["code"] == "VISION_UNSUPPORTED"
    assert (await client.get(f"/v1/sessions/{session['id']}/feedback")).json()["items"] == []


async def test_feedback_analysis_keeps_progress_saved_while_model_runs(
    client,
    monkeypatch,
):
    session, _ = await setup_plan(client, monkeypatch)
    media = (await upload(client, image_bytes(), "image/jpeg", "photo.jpg", "image")).json()
    started = asyncio.Event()
    release = asyncio.Event()
    fake = fake_vision(media["id"])

    async def hanging_chat(
        system_prompt,
        user_prompt,
        model=None,
        timeout_s=None,
        vision_images=None,
    ):
        started.set()
        await release.wait()
        return await fake(system_prompt, user_prompt, model, timeout_s, vision_images)

    monkeypatch.setattr(client.app.state.model_client, "chat_json", hanging_chat)
    response = await client.post(
        f"/v1/sessions/{session['id']}/feedback-jobs",
        json={
            "step_id": "step_1",
            "plan_version": 1,
            "media_ids": [media["id"]],
        },
    )
    assert response.status_code == 202, response.text
    await asyncio.wait_for(started.wait(), timeout=5)

    timer = {
        "step_id": "step_1",
        "state": "running",
        "duration_s": 300,
        "remaining_s": 300,
        "anchor_elapsed_ms": 1000,
        "saved_at_epoch_ms": 1793789100000,
        "updated_at": "2026-11-04T08:05:00Z",
    }
    patched = await client.patch(
        f"/v1/sessions/{session['id']}/progress",
        json={
            "base_plan_version": 1,
            "current_step_id": "step_1",
            "step_statuses": {"step_1": "in_progress"},
            "timer": timer,
        },
    )
    assert patched.status_code == 200, patched.text

    release.set()
    job = await wait_job(client, response.json()["id"])
    assert job["status"] == "succeeded", job

    fresh = (await client.get(f"/v1/sessions/{session['id']}")).json()
    progress = fresh["progress"]
    assert fresh["current_plan_version"] == 1
    assert fresh["status"] == "in_progress"
    assert progress["current_step_id"] == "step_1"
    assert progress["step_statuses"] == {"step_1": "in_progress"}
    assert progress["timer"] == timer
    assert progress["evidence_levels"]["step_1"] == "model_observed"


async def test_feedback_analysis_does_not_write_after_revision_changes_plan(
    client,
    monkeypatch,
):
    session, _ = await setup_plan(client, monkeypatch)
    media = (await upload(client, image_bytes(), "image/jpeg", "photo.jpg", "image")).json()
    started = asyncio.Event()
    release = asyncio.Event()
    fake = fake_vision(media["id"])
    calls = {"count": 0}

    async def chat(
        system_prompt,
        user_prompt,
        model=None,
        timeout_s=None,
        vision_images=None,
    ):
        calls["count"] += 1
        if calls["count"] == 1:
            started.set()
            await release.wait()
            return await fake(system_prompt, user_prompt, model, timeout_s, vision_images)
        return {
            "changes": [
                {
                    "op": "update",
                    "step_id": "step_2",
                    "after": {"duration_s": 90},
                    "reason": "缩短炒制时间。",
                }
            ]
        }

    monkeypatch.setattr(client.app.state.model_client, "chat_json", chat)
    feedback_response = await client.post(
        f"/v1/sessions/{session['id']}/feedback-jobs",
        json={
            "step_id": "step_1",
            "plan_version": 1,
            "media_ids": [media["id"]],
        },
    )
    assert feedback_response.status_code == 202, feedback_response.text
    await asyncio.wait_for(started.wait(), timeout=5)

    revision_response = await client.post(
        f"/v1/sessions/{session['id']}/revision-jobs",
        json={
            "feedback_id": None,
            "base_plan_version": 1,
            "request_reason": "缩短炒制时间。",
        },
    )
    assert revision_response.status_code == 202, revision_response.text
    revision_job = await wait_job(client, revision_response.json()["id"])
    assert revision_job["status"] == "succeeded", revision_job
    revision_id = revision_job["result"]["revision_id"]
    applied = await client.post(
        f"/v1/sessions/{session['id']}/revisions/{revision_id}/apply",
        json={"base_plan_version": 1},
    )
    assert applied.status_code == 200, applied.text
    assert applied.json()["plan"]["version"] == 2

    release.set()
    feedback_job = await wait_job(client, feedback_response.json()["id"])
    assert feedback_job["status"] == "failed"
    assert feedback_job["error"]["error"]["code"] == "VERSION_CONFLICT"
    assert feedback_job["error"]["error"]["details"]["current_plan_version"] == 2

    fresh = (await client.get(f"/v1/sessions/{session['id']}")).json()
    assert fresh["current_plan_version"] == 2
    assert fresh["progress"]["step_statuses"] == {}
    assert fresh["progress"]["evidence_levels"]["step_1"] == "media_submitted"
    assert (await client.get(f"/v1/sessions/{session['id']}/feedback")).json()["items"] == []
    assert await client.app.state.store.list_feedback(session["id"]) == []