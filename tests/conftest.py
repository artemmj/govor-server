"""Глобальная конфигурация pytest для проекта.

Этот файл отвечает за подготовку окружения для тестов:
- создаёт тестовую БД,
- создаёт схему таблиц,
- даёт каждому тесту отдельную сессию,
- подменяет зависимости приложения,
- помогает быстро создавать пользователей для auth-тестов.
"""

import asyncio
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session, sessionmaker

from dependencies.db import db_dependency
from govor_server.main import app
from handlers.auth import AuthHandler
from models import Base, User
from settings import settings
from tests.factories.user import UserFactory

# Путь к тестовой базе данных. Важно, чтобы тесты не трогали основную БД проекта.
TEST_SQLALCHEMY_DATABASE_URL: str = settings.db_settings.test_db_url
engine: Engine = create_engine(TEST_SQLALCHEMY_DATABASE_URL)
admin_engine: Engine = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL, isolation_level="AUTOCOMMIT"
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_test_database() -> None:
    """Создаёт базу данных для тестов, если она ещё не существует.

    Это нужно, потому что проект использует PostgreSQL, а для изолированных тестов
    лучше иметь отдельную БД с тестовой схемой.
    """
    with admin_engine.connect() as connection:
        try:
            connection.execute(
                text(f"CREATE DATABASE {TEST_SQLALCHEMY_DATABASE_URL.split('/')[-1]}")
            )
        except ProgrammingError:
            print("Database already exists, continuing...")


@pytest.fixture(scope="session", autouse=True)
def setup_test_database() -> Generator[None, None, None]:
    """Подготавливает схему БД один раз на весь прогон тестов.

    Фикстура autouse=True означает, что она запускается автоматически перед каждым тестом
    в этой сессии. Это гарантирует, что таблицы уже есть до выполнения тестов.
    """
    create_test_database()
    Base.metadata.create_all(bind=engine)
    yield
    # Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Возвращает отдельную SQLAlchemy-сессию для каждого теста.

    На каждом тесте мы создаём отдельное соединение и транзакцию. Это нужно для изоляции:
    один тест не должен видеть данные другого теста.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Возвращает FastAPI TestClient, который работает с тестовой БД.

    Мы подменяем зависимость `db_dependency`, чтобы приложение при запросе брало не
    основную сессию, а именно эту тестовую. Это главный инструмент для API-тестов.
    """

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[db_dependency] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def ordinary_user(db_session: Session) -> User:
    """Создаёт обычного пользователя для тестов без лишнего кода."""
    return UserFactory.create(session=db_session)


@pytest.fixture
def client_user(client: TestClient, db_session: Session) -> Generator[TestClient, None, None]:
    """Создаёт пользователя и сразу кладёт JWT в заголовок Authorization.

    Это удобно для тестов, где нужно проверить защищённый endpoint, который требует
    авторизацию.
    """
    user = UserFactory.create(session=db_session, password="password")
    token, _ = asyncio.run(AuthHandler().create_access_token(user.id))
    client.headers.update({"Authorization": f"Bearer {token}"})
    yield client
    client.headers.pop("Authorization", None)
