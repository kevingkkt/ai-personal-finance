import requests

BACKEND_URL = "http://127.0.0.1:5004"
DATABASE_URL = "http://127.0.0.1:6004"
def test_database_health():
    response = requests.get(f"{DATABASE_URL}/health")
    assert response.status_code == 200
def test_backend_health():
    response = requests.get(f"{BACKEND_URL}/health")
    assert response.status_code == 200


#need one for the getting bills  backend
def test_get_bills():
    r =  requests.get(f"{BACKEND_URL}/bills")
    assert r.status_code == 200

    data = r.json()
#The default is more than 2 so it works ok
    assert isinstance(data, list)
    assert len(data) >= 2



#end point check
def test_get_a_single_bill():
    response = requests.get(f"{BACKEND_URL}/bills/1")
    assert response.status_code == 200
    data = response.json()
    assert "bill_id" in data
    assert "payment_status" in data
    assert "due_date" in data
    assert "amount" in data
    assert "description" in data





# def test_bills_ai_insights():
#     response = requests.post(
#         f"{BACKEND_URL}/ai-insights",
#         json={
#             "input": "How am I able to make sure I pay my bills on time?"
#         },
#         timeout=600
#     )
#     assert response.status_code == 200
#     d = response.json()
#     assert "insight" in d
#     assert isinstance(d["insight"], str)
#     assert len(d["insight"]) > 0