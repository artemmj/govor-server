"""Тесты для auth-сценариев.

Здесь проверяется не просто "может ли код работать вообще", а конкретное поведение
API: логин должен выдавать JWT только для корректного пользователя и корректного пароля.
"""

from contextlib import asynccontextmanager

from fastapi.testclient import TestClient

from govor_server.main import app
from handlers.auth import AuthHandler
from models.user import User
from services.auth import AuthService, get_auth_service
from tests.factories.user import UserFactory


class _FakeRedis:
    """Поддельный Redis для тестов.

    В auth-логике сервис пытается сохранять токен в Redis. В teset-окружении нет
    необходимости работать с реальным Redis, поэтому мы подменяем его "пустой"
    заглушкой.
    """

    @asynccontextmanager
    async def get_client(self):
        class _FakeRedisClient:
            async def set(self, *args, **kwargs):
                return None

            async def get(self, *args, **kwargs):
                return None

        yield _FakeRedisClient()


class _SessionUserDAO:
    """DAO-обёртка над текущей SQLAlchemy-сессией.

    Эта заглушка нужна для того, чтобы endpoint срабатывал на реальной БД из теста,
    а не пытался достать данные через отдельный async-слой приложения.
    """

    def __init__(self, session):
        self.session = session

    async def get_by_phone(self, phone: str):
        user = self.session.query(User).filter_by(phone=phone).one_or_none()
        if user is None:
            return None

        return {
            "id": user.id,
            "email": user.email,
            "phone": user.phone,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "password_hash": user.password_hash,
        }


def test_get_access_token_returns_jwt_for_valid_credentials(
    client: TestClient, db_session
) -> None:
    """Тестирует реальный API endpoint /auth/login.

    Сценарий:
    1. Создаём пользователя в тестовой БД.
    2. Коммитим его, чтобы запись стала видима приложению.
    3. Отправляем POST /auth/login.
    4. Проверяем, что сервер отвечает 200 и возвращает access_token.
    """
    user = UserFactory.create(session=db_session, password="password")
    db_session.commit()

    app.dependency_overrides[get_auth_service] = lambda: AuthService(
        user_dao=_SessionUserDAO(db_session),
        auth_handler=AuthHandler(),
        redis=_FakeRedis(),
    )

    try:
        response = client.post(
            "/auth/login",
            json={"phone": user.phone, "password": "password"},
        )
    finally:
        app.dependency_overrides.clear()

    payload = response.json()
    assert response.status_code == 200
    assert "access_token" in payload
    assert payload["access_token"]


# def test_verify_token_returns_user_email(client_user: TestClient) -> None:
#     response = client_user.post("/login/verify-token")

#     assert response.status_code == 200
#     assert "email" in response.json()


# def test_password_recovery_for_missing_email_returns_created(
#     client: TestClient,
# ) -> None:
#     email = Faker().email()

#     response = client.post(f"/login/password-recovery/{email}")

#     assert response.status_code == 201


# def test_password_recovery_for_existing_email_returns_success(
#     client: TestClient, ordinary_user: User
# ) -> None:
#     response = client.post(f"/login/password-recovery/{ordinary_user.email}")

#     assert response.status_code == 200
