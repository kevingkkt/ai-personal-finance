import requests

BACKEND_URL = "http://127.0.0.1:5004"
DATABASE_URL = "http://127.0.0.1:5003"


def test_backend_health():
    response = requests.get(f"{BACKEND_URL}/health")
    assert response.status_code == 200


def test_database_health():
    response = requests.get(f"{DATABASE_URL}/health")
    assert response.status_code == 200


def test_get_transactions():
    response = requests.get(f"{BACKEND_URL}/budgets")
    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 10


def test_get_single_transaction():
    response = requests.get(f"{BACKEND_URL}/budgets/1")
    assert response.status_code == 200

    data = response.json()

    assert "id" in data
    assert "name" in data
    assert "amount" in data


def test_invalid_transaction():
    response = requests.get(f"{BACKEND_URL}/budgets/9999")
    assert response.status_code == 404

def test_ai_insights():
    response = requests.get(
        f"{BACKEND_URL}/ai-insights",
        timeout=300
    )

    assert response.status_code == 200

    data = response.json()

    assert "insight" in data
    assert "Total Income:" in data["insight"]
    assert "Total Expenses:" in data["insight"]