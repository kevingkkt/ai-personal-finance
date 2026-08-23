import requests

BASE_URL = "http://127.0.0.1:5001"


def test_get_transactions():
    response = requests.get(f"{BASE_URL}/transactions")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 10


def test_get_single_transaction():
    response = requests.get(f"{BASE_URL}/transactions/1")

    assert response.status_code == 200

    data = response.json()

    assert "id" in data
    assert "type" in data
    assert "category" in data
    assert "amount" in data


def test_invalid_transaction():
    response = requests.get(f"{BASE_URL}/transactions/9999")

    assert response.status_code == 404


def test_ai_insights():
    response = requests.get(
        f"{BASE_URL}/ai-insights",
        timeout=120
    )

    assert response.status_code == 200

    data = response.json()

    assert "insight" in data
    assert len(data["insight"]) > 0