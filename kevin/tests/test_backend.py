import requests

BACKEND_URL = "http://127.0.0.1:5001"
DATABASE_URL = "http://127.0.0.1:5002"


def test_backend_health():
    response = requests.get(f"{BACKEND_URL}/health")
    assert response.status_code == 200


def test_database_health():
    response = requests.get(f"{DATABASE_URL}/health")
    assert response.status_code == 200


def test_get_transactions():
    response = requests.get(f"{BACKEND_URL}/transactions")
    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 10


def test_get_single_transaction():
    response = requests.get(f"{BACKEND_URL}/transactions/1")
    assert response.status_code == 200

    data = response.json()

    assert "id" in data
    assert "type" in data
    assert "category" in data
    assert "amount" in data


def test_invalid_transaction():
    response = requests.get(f"{BACKEND_URL}/transactions/9999")
    assert response.status_code == 404


def test_htmx_transactions():
    response = requests.get(f"{BACKEND_URL}/transactions-html")
    assert response.status_code == 200
    assert "<table>" in response.text
    assert "Salary" in response.text


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