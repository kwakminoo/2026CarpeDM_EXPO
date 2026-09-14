from random import Random
from types import SimpleNamespace as NS

from app.services import interaction
from app.services.workplace import pick_workplace_episodes


def _categories():
    return [
        {"id": "onboarding", "label": "출근·적응", "orders": [1, 2, 3]},
        {"id": "priority", "label": "업무 지시·우선순위", "orders": [4, 5, 6]},
        {"id": "report", "label": "보고·피드백", "orders": [7, 8, 9]},
        {"id": "meeting", "label": "미팅·협업", "orders": [10, 11, 12]},
        {"id": "leaving", "label": "퇴근·관계", "orders": [13, 14, 15]},
    ]


def _episodes():
    return [
        NS(id=order, order=order, title=f"장면 {order}", situation=f"상황 {order}",
           initial_question=f"대사 {order}",
           checklist=[{"id": "g", "tip": f"팁 {order}", "keywords": ["자료 확인"]}])
        for order in range(1, 16)
    ]


def test_pick_one_scene_per_category_is_stable_with_seed():
    scenario = NS(world_setting={"workplace_categories": _categories()})
    first = pick_workplace_episodes(scenario, _episodes(), Random(7))
    second = pick_workplace_episodes(scenario, _episodes(), Random(7))
    assert [episode.order for episode in first] == [episode.order for episode in second]
    assert [episode.order for episode in first] == [2, 4, 8, 12, 13]


def test_workplace_session_advances_one_category_per_answer():
    session = NS(rapport={})
    scenario = NS(world_setting={"workplace_categories": _categories()})
    interaction.initialize(session, scenario, _episodes(), "workplace", rng=Random(7))
    briefing = interaction.public_state(session)["briefing"]
    assert briefing["step"] == 1 and briefing["category_label"] == "출근·적응"
    assert briefing["situation"] == "상황 2"
    for step in range(4):
        result = interaction.advance(session, NS(response_text="답변", question_type="initial" if step == 0 else "main"), [])
        assert not result["finished"]
        assert interaction.public_state(session)["briefing"]["step"] == step + 2
    result = interaction.advance(session, NS(response_text="답변", question_type="main"), [])
    assert result["finished"] and result["reason"] == "questions_completed"
    assert "briefing" not in interaction.public_state(session)


def test_training_ignores_workplace_pack_slug():
    from fastapi.testclient import TestClient

    from app.main import app
    from app.seed.run import seed

    seed()
    created = TestClient(app).post("/api/sessions", json={
        "service_mode": "training",
        "scenario_slug": "workplace-conversation",
        "mode": 5,
        "consent": {"agreed": True, "storage_policy": "none"},
    })
    assert created.status_code == 200, created.text
    assert created.json()["scenario"]["slug"] != "workplace-conversation"


def test_workplace_without_categories_uses_training_flow():
    session = NS(rapport={})
    episode = NS(id=1, checklist=[{"id": "g", "label": "목표", "keywords": ["자료 확인"], "followup": "이어서 말씀해 주세요."}])
    interaction.initialize(session, NS(world_setting={}), [episode], "workplace")
    assert interaction.state(session)["mode"] == "training"


def test_workplace_api_starts_with_briefing_and_script_line():
    from fastapi.testclient import TestClient

    from app.main import app
    from app.seed.run import seed

    seed()
    created = TestClient(app).post("/api/sessions", json={
        "service_mode": "workplace",
        "mode": 5,
        "consent": {"agreed": True, "storage_policy": "none"},
    })
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["scenario"]["slug"] == "workplace-conversation"
    briefing = body["interaction"]["briefing"]
    assert briefing["total"] == 5
    assert briefing["step"] == 1
    assert briefing["situation"]
    assert briefing["tip"]
    assert body["current_turn"]["question_type"] == "initial"
    assert body["current_turn"]["question_text"]
