from models.user import User
from tests.factories.user import UserFactory


def test_user_is_created_in_database(db_session) -> None:
    """Проверяет, что пользователь реально сохраняется в БД.

    Сценарий:
    1. создаём пользователя через фабрику;
    2. подгружаем данные в текущую сессию;
    3. запросом в ту же сессию проверяем, что запись появилась;
    4. убеждаемся, что поля `id`, `phone` и `password_hash` заполнены.

    Этот тест нужен для проверки уровня persistence: сохранение модели в хранилище.
    """
    user = UserFactory.create(session=db_session, password="password")
    db_session.flush()
    db_session.refresh(user)

    saved_user = db_session.query(User).filter_by(phone=user.phone).one()

    assert saved_user.id == user.id
    assert saved_user.phone == user.phone
    assert saved_user.password_hash
