from __future__ import annotations

FULL_COOKING = {
    "skill_level": "beginner",
    "time_budget_min": 30,
    "people": 2,
    "servings": 2,
    "stove_type": "gas",
}


def answer_for(question):
    if question["kind"] == "single_choice":
        return question["options"][0]
    if question["kind"] == "multi_choice":
        return [question["options"][0]]
    if question["kind"] == "number":
        return 30 if question["field"] == "time_budget_min" else 2
    if question["kind"] == "boolean":
        return True
    return "无"


async def test_create_session_without_conditions_returns_three_to_five_questions(client):
    response = await client.post(
        "/v1/sessions",
        json={"domain": "cooking", "goal": "2 人份番茄鸡蛋面，30 分钟内完成"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "clarifying"
    assert 3 <= len(body["questions"]) <= 5
    assert body["current_plan_version"] is None
    assert body["progress"]["step_statuses"] == {}


async def test_create_session_with_full_conditions_is_ready(client):
    response = await client.post(
        "/v1/sessions",
        json={"domain": "cooking", "goal": "2 人份番茄鸡蛋面", "conditions": FULL_COOKING},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "ready"
    assert body["questions"] == []


async def test_answers_finish_within_two_rounds(client):
    response = await client.post(
        "/v1/sessions",
        json={"domain": "cooking", "goal": "2 人份番茄鸡蛋面"},
    )
    session = response.json()
    rounds = 0
    while session["status"] == "clarifying":
        rounds += 1
        assert rounds <= 2
        answers = [
            {"question_id": question["id"], "value": answer_for(question)}
            for question in session["questions"]
        ]
        answered = await client.post(
            f"/v1/sessions/{session['id']}/answers",
            json={"answers": answers},
        )
        assert answered.status_code == 200
        session = answered.json()
    assert session["status"] == "ready"
    assert session["questions"] == []


async def test_key_condition_null_is_rejected_atomically(client):
    response = await client.post(
        "/v1/sessions",
        json={
            "domain": "cooking",
            "goal": "2 人份番茄鸡蛋面",
            "conditions": {"time_budget_min": None},
        },
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "INVALID_REQUEST"
    assert body["error"]["details"]["field"] == "time_budget_min"
    assert body["error"]["details"]["reason"] == "key_condition_null"


async def test_invalid_domain_is_rejected(client):
    response = await client.post(
        "/v1/sessions",
        json={"domain": "gardening", "goal": "种一盆番茄"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_REQUEST"

async def test_text_answers_for_array_conditions_are_normalized(client):
    response = await client.post(
        "/v1/sessions",
        json={
            "domain": "cooking",
            "goal": "2 人份番茄鸡蛋面",
            "conditions": {
                "skill_level": "beginner",
                "time_budget_min": 30,
                "people": 2,
                "servings": 2,
            },
        },
    )
    session = response.json()
    questions = {item["field"]: item for item in session["questions"]}
    assert "stove_type" in questions
    answers = [
        {"question_id": questions["stove_type"]["id"], "value": "gas"},
        {"question_id": questions["allergies"]["id"], "value": "花生、牛奶"},
        {"question_id": questions["available_equipment"]["id"], "value": "炒锅、汤锅"},
        {"question_id": questions["oven_available"]["id"], "value": False},
    ]
    answered = await client.post(
        f"/v1/sessions/{session['id']}/answers",
        json={"answers": answers},
    )
    assert answered.status_code == 200, answered.text
    body = answered.json()
    assert body["status"] == "ready"
    assert body["conditions"]["allergies"] == ["花生", "牛奶"]
    assert body["conditions"]["available_equipment"] == ["炒锅", "汤锅"]


async def test_none_text_answer_normalizes_to_empty_array(client):
    response = await client.post(
        "/v1/sessions",
        json={
            "domain": "cooking",
            "goal": "2 人份番茄鸡蛋面",
            "conditions": {
                "skill_level": "beginner",
                "time_budget_min": 30,
                "people": 2,
                "servings": 2,
            },
        },
    )
    session = response.json()
    questions = {item["field"]: item for item in session["questions"]}
    answers = [
        {"question_id": questions["stove_type"]["id"], "value": "gas"},
        {"question_id": questions["allergies"]["id"], "value": "无"},
        {"question_id": questions["available_equipment"]["id"], "value": "炒锅"},
        {"question_id": questions["oven_available"]["id"], "value": False},
    ]
    answered = await client.post(
        f"/v1/sessions/{session['id']}/answers",
        json={"answers": answers},
    )
    assert answered.status_code == 200, answered.text
    assert answered.json()["conditions"]["allergies"] == []

async def test_two_round_clarification_allows_skipping_optional_questions(client):
    created = await client.post(
        "/v1/sessions",
        json={"domain": "cooking", "goal": "2 人份番茄鸡蛋面"},
    )
    session = created.json()
    first_fields = {item["field"]: item for item in session["questions"]}
    assert set(first_fields) == {
        "skill_level",
        "time_budget_min",
        "people",
        "servings",
        "stove_type",
    }

    first_answers = [
        {"question_id": first_fields["skill_level"]["id"], "value": "beginner"},
        {"question_id": first_fields["time_budget_min"]["id"], "value": 30},
    ]
    first_response = await client.post(
        f"/v1/sessions/{session['id']}/answers",
        json={"answers": first_answers},
    )
    assert first_response.status_code == 200
    session = first_response.json()
    assert session["status"] == "clarifying"
    assert 3 <= len(session["questions"]) <= 5
    second_fields = {item["field"]: item for item in session["questions"]}
    assert {"people", "servings", "stove_type"} <= set(second_fields)

    second_answers = [
        {"question_id": second_fields["people"]["id"], "value": 2},
        {"question_id": second_fields["servings"]["id"], "value": 2},
        {"question_id": second_fields["stove_type"]["id"], "value": "gas"},
    ]
    second_response = await client.post(
        f"/v1/sessions/{session['id']}/answers",
        json={"answers": second_answers},
    )
    assert second_response.status_code == 200
    final = second_response.json()
    assert final["status"] == "ready"
    assert final["questions"] == []
    assert final["conditions"]["skill_level"] == "beginner"
    assert final["conditions"]["time_budget_min"] == 30
    assert final["conditions"]["people"] == 2
    assert final["conditions"]["servings"] == 2
    assert final["conditions"]["stove_type"] == "gas"
    assert "oven_available" not in final["conditions"]
    assert "allergies" not in final["conditions"]


async def test_optional_question_can_be_skipped_when_key_fields_suffice(client):
    created = await client.post(
        "/v1/sessions",
        json={
            "domain": "cooking",
            "goal": "2 人份番茄鸡蛋面",
            "conditions": {
                "skill_level": "beginner",
                "time_budget_min": 30,
                "people": 2,
                "servings": 2,
            },
        },
    )
    session = created.json()
    fields = {item["field"]: item for item in session["questions"]}
    assert {"stove_type", "oven_available", "allergies", "available_equipment"} <= set(fields)
    answered = await client.post(
        f"/v1/sessions/{session['id']}/answers",
        json={
            "answers": [
                {"question_id": fields["stove_type"]["id"], "value": "gas"},
            ]
        },
    )
    assert answered.status_code == 200
    final = answered.json()
    assert final["status"] == "ready"
    assert final["questions"] == []
    assert "oven_available" not in final["conditions"]
    assert "allergies" not in final["conditions"]
