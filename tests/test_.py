from fastapi.testclient import TestClient


def test_my_car_toyota(setup_test_database, my_car: str):
    assert my_car == "Toyota"


def test_my_car_honda(setup_test_database, my_car: str):
    assert my_car != "Honda"


def test_health(setup_test_database, client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
