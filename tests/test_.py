from fastapi.testclient import TestClient


def test_my_car_toyota(my_car: str):
    assert my_car == "Toyota"

def test_my_car_honda(my_car: str):
    assert my_car != "Honda"

def test_health(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
