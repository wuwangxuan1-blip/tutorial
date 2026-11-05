from __future__ import annotations

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