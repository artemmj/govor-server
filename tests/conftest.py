from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from collections.abc import Generator

import pytest
from sqlalchemy import text, create_engine
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import sessionmaker

from models import Base, User
from settings import settings
from dependencies.db import db_dependency
from govor_server.main import app
from handlers.auth import AuthHandler

from tests.factories.user import UserFactory
from tests.constants.user import UserTestConstants

@pytest.fixture
def my_car() -> str:
    return "Toyota"


TEST_SQLALCHEMY_DATABASE_URL: str = settings.db_settings.test_db_url
admin_engine = create_engine(
   TEST_SQLALCHEMY_DATABASE_URL, isolation_level="AUTOCOMMIT"
)
engine = create_engine(TEST_SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_test_database():
    """Create the test database if it doesn't exist."""
    with admin_engine.connect() as connection:
        try:
            connection.execute(
                text(f"CREATE DATABASE {TEST_SQLALCHEMY_DATABASE_URL.split('/')[-1]}")
            )
        except ProgrammingError:
            print("Database already exists, continuing...")


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Create the test database schema before any tests run,
    and drop it after all tests are done.
    """
    create_test_database()
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator:
    """
    Create a new database session for each test and roll it back after the test.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """
    Provide a TestClient that uses the test database session.
    Override the get_db dependency to use the test session.
    """
    
    def override_get_db():
        yield db
    app.dependency_overrides[db_dependency] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client_superuser(client: TestClient) -> Generator[TestClient, None, None]:
    """
    Fixture that returns a TestClient with superuser authentication headers.
    It also creates a user in DB.
    """
    user: User = UserFactory(
        is_superuser=True,
        email=UserTestConstants.CLIENT_SUPERUSER_EMAIL,
        password=UserTestConstants.CLIENT_SUPERUSER_PASSWORD,
    )
    access_token: str = AuthHandler().security.create_access_token(user.id)
    headers = {"Authorization": f"Bearer {access_token}"}
    # Modify the client to automatically include the superuser headers in each request
    client.headers.update(headers)
    yield client
    # Clean up: Remove the superuser headers after the test
    client.headers.clear()


@pytest.fixture(scope="function")
def client_user(client: TestClient) -> Generator[TestClient, None, None]:
    """
    Fixture that returns a TestClient with authentication headers. It also creates a user in DB.
    """
    user: User = UserFactory()
    access_token: str = AuthHandler().security.create_access_token(user.id)
    headers = {"Authorization": f"Bearer {access_token}"}
    client.headers.update(headers)
    yield client
    client.headers.clear()
