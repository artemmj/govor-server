import factory

from models.user import User
from handlers.auth import AuthHandler
from tests.constants.user import UserTestConstants


class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = User  # SQLAlchemy model
        sqlalchemy_session_persistence = (
            "commit"  # Commit the session after creating the user instance.
        )

    email = factory.Faker("email")
    phone = factory.Faker("phone_number", locale="ru_RU")
    password_hash = factory.LazyFunction(
        lambda: AuthHandler().get_password_hash(UserTestConstants.USER_DEFAULT_PASSWORD)
    )
    is_active = True
    is_superuser = False

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        # Handle the password argument before creating the user
        if "password" in kwargs:
            kwargs["hashed_password"] = AuthHandler().get_password_hash(
                kwargs.pop("password")
            )
        return super()._create(model_class, *args, **kwargs)
