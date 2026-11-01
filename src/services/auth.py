import uuid

from fastapi import status

from dao.user import UserDAO
from dependencies.db import db_dependency
from dependencies.redis import redis_dependency, RedisDependency
from handlers.auth import AuthHandler
from schemas.auth import LoginRequest, LoginResponse
from exceptions import (
    AccountDisabledOrBannedException,
    WrongEmailPasswordException,
)


class AuthService:
    def __init__(
        self, user_dao: UserDAO, auth_handler: AuthHandler, redis: RedisDependency
    ):
        self.user_dao = user_dao
        self.auth_handler = auth_handler
        self.redis = redis

    async def _store_access_token(
        self, token: str, user_id: uuid.UUID, session_id: str
    ) -> None:
        async with self.redis.get_client() as client:
            await client.set(f"{user_id}:{session_id}", token)

    async def get_access_token(self, user_id: uuid.UUID, session_id: str) -> str | None:
        async with self.redis.get_client() as client:
            return await client.get(f"{user_id}:{session_id}")

    async def create_and_store_access_token(
        self, user_id: uuid.UUID
    ) -> tuple[str, str]:
        token, session_id = await self.auth_handler.create_access_token(user_id)
        await self._store_access_token(token, user_id, session_id)
        return token, session_id

    async def login(self, creds: LoginRequest) -> LoginResponse:
        exist_user = await self.user_dao.get_by_phone(phone=creds.phone)
        if exist_user is None or not await self.auth_handler.verify_password(
            creds.password, exist_user["password_hash"]
        ):
            raise WrongEmailPasswordException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Wrong email or password",
            )
        if not exist_user["is_active"] or exist_user["is_banned"]:
            raise AccountDisabledOrBannedException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled or banned",
            )
        token, session_id = await self.create_and_store_access_token(exist_user["id"])
        return LoginResponse(access_token=token, session_id=session_id)


def get_auth_service() -> AuthService:
    """Фабрика сервиса."""
    return AuthService(
        user_dao=UserDAO(db_dependency),
        auth_handler=AuthHandler(),
        redis=redis_dependency,
    )
