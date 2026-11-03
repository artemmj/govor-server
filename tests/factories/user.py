import asyncio

import factory

from handlers.auth import AuthHandler
from models.user import User


def build_password_hash(password: str) -> str:
    """Генерирует хеш пароля через тот же AuthHandler, что и в приложении.

    Важно использовать тот же механизм хеширования, иначе тесты будут проверять не то,
    что реально использует система в production.
    """
    return asyncio.run(AuthHandler().get_password_hash(password))


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Создаёт пользователя и сразу сохраняет его в указанную SQLAlchemy-сессию.

    `factory_boy` автоматически создаёт поля модели: email, phone, password_hash и т.д.
    Мы переопределяем `_create`, чтобы:
    - принимать параметр `password` и хешировать его;
    - привязывать создание к конкретной `session` из pytest;
    - сохранять сущность в тестовой БД без лишнего кода в тестах.
    """

    class Meta:
        model = User
        sqlalchemy_session_persistence = "flush"

    email = factory.Faker("email")
    phone = factory.Sequence(lambda n: f"790000000{n:02d}")
    password_hash = factory.LazyFunction(lambda: build_password_hash("password"))
    is_active = True
    is_superuser = False

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Переопределяем создание объекта, чтобы корректно обработать пароль."""
        password = kwargs.pop("password", None)
        session = kwargs.pop("session", None)

        if session is not None:
            cls._meta.sqlalchemy_session = session

        if password is not None:
            kwargs["password_hash"] = build_password_hash(password)

        return super()._create(model_class, *args, **kwargs)
