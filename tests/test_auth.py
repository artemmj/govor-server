from faker import Faker
from fastapi.testclient import TestClient

from src.settings import settings
from src.models.user import User

from .factories.user import UserFactory


def test_get_access_token(client: TestClient) -> None:
     password: str = "password"
     user: User = UserFactory(password=password)
     login_data: dict = {
        "username": user.email,
        "password": password,
     }
     r = client.post(f"{settings.API_V1_STR}/login/get-access-token", data=login_data)
     tokens: dict = r.json()
     assert r.status_code == 200
     assert "access_token" in tokens
     assert tokens["access_token"]


def test_use_access_token(client: TestClient, client_user: TestClient) -> None:
    r = client_user.post(
        f"{settings.API_V1_STR}/login/verify-token",
    )
    result = r.json()
    assert r.status_code == 200
    assert "email" in result


def test_forgot_email_not_existing_email(client: TestClient) -> None:
    email = Faker().email()
    r = client.post(f"{settings.API_V1_STR}/login/password-recovery/{email}")
    assert r.status_code == 201


def test_forgot_email_existing_email(client: TestClient, ordinary_user: User) -> None:
    email = ordinary_user.email
    r = client.post(f"{settings.API_V1_STR}/login/password-recovery/{email}")
    assert r.status_code == 200
