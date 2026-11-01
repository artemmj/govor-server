import datetime
import uuid
from typing import Tuple

import jwt
import bcrypt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from settings import settings


class AuthHandler:
    """Утилитарный класс для работы с безопасностью: хеширование паролей и JWT."""

    def __init__(self):
        # bcrypt автоматически управляет солью
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.secret_key = settings.secret_key
        self.algorithm = "HS256"

    async def get_password_hash(self, password: str) -> str:
        """Хеширует пароль с использованием bcrypt."""
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    async def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Проверяет соответствие пароля его хешу."""
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )

    async def create_access_token(self, user_id: uuid.UUID) -> Tuple:
        """
        Создает JWT токен и уникальный ID сессии.
        """
        expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            seconds=settings.access_token_expire
        )
        session_id = str(uuid.uuid4())
        to_encode = {
            "sub": str(user_id),
            "user_id": str(user_id),
            "session_id": session_id,
            "exp": expire,
            "iat": datetime.datetime.now(datetime.timezone.utc),
            "type": "access",
        }

        encoded_jwt = jwt.encode(
            to_encode, self.secret_key.get_secret_value(), algorithm=self.algorithm
        )
        return encoded_jwt, session_id

    async def decode_access_token(self, token: str) -> dict:
        """
        Декодирует и валидирует JWT токен.
        """
        try:
            payload = jwt.decode(
                token, self.secret_key.get_secret_value(), algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
