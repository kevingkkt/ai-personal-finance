import requests

BACKEND_URL = "http://127.0.0.1:5003"
DATABASE_URL = "http://127.0.0.1:6003"


def get_sample_goal():
    response = requests.get(
        f"{BACKEND_URL}/goals",
        timeout=10
    )

    assert response.status_code == 200

    goals = response.json()

    assert isinstance(goals, list)
    assert len(goals) > 0

    return goals[0]


def test_backend_health():
    response = requests.get(
        f"{BACKEND_URL}/health",
        timeout=10
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_database_health():
    response = requests.get(
        f"{DATABASE_URL}/",
        timeout=10
    )

    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_get_goals():
    response = requests.get(
        f"{BACKEND_URL}/goals",
        timeout=10
    )

    assert response.status_code == 200

    goals = response.json()

    assert isinstance(goals, list)
    assert len(goals) >= 10


def test_get_single_goal():
    goal = get_sample_goal()

    response = requests.get(
        f"{BACKEND_URL}/goals/{goal['id']}",
        timeout=10
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == goal["id"]
    assert "goal_name" in data
    assert "target_amount" in data
    assert "current_amount" in data
    assert "target_date" in data


def test_invalid_goal():
    response = requests.get(
        f"{BACKEND_URL}/goals",
        timeout=10
    )

    assert response.status_code == 200

    goals = response.json()

    missing_id = max(
        (goal["id"] for goal in goals),
        default=0
    ) + 1

    response = requests.get(
        f"{BACKEND_URL}/goals/{missing_id}",
        timeout=10
    )

    assert response.status_code == 404
    assert "error" in response.json()


def test_get_contributions():
    goal = get_sample_goal()

    response = requests.get(
        f"{BACKEND_URL}/goals/{goal['id']}/contributions",
        timeout=10
    )

    assert response.status_code == 200

    contributions = response.json()

    assert isinstance(contributions, list)

    for contribution in contributions:
        assert "id" in contribution
        assert contribution["goal_id"] == goal["id"]
        assert "amount" in contribution
        assert "contribution_date" in contribution


def test_backend_matches_database():
    backend_response = requests.get(
        f"{BACKEND_URL}/goals",
        timeout=10
    )

    database_response = requests.get(
        f"{DATABASE_URL}/goals",
        timeout=10
    )

    assert backend_response.status_code == 200
    assert database_response.status_code == 200

    assert backend_response.json() == database_response.json()


def test_ai_insights():
    goal = get_sample_goal()

    response = requests.post(
        f"{BACKEND_URL}/ai-insights",
        json={
            "goal_id": goal["id"],
            "input": "Give one short suggestion for this savings goal."
        },
        timeout=660
    )

    assert response.status_code == 200

    data = response.json()

    assert data["goal_id"] == goal["id"]
    assert "model" in data
    assert isinstance(data.get("insight"), str)
    assert data["insight"].strip()