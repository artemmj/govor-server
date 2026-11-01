import uuid
from typing import List, Optional

from dao.user import UserDAO
from dependencies.db import db_dependency
from handlers.auth import AuthHandler
from schemas.user import UserSchema, UserCreateRequest, UserUpdateRequest
from exceptions import (
    UserAlreadyExistsError,
    UserNotFoundError,
    UpdateUserNeedFields,
)


class UsersService:
    def __init__(self, user_dao: UserDAO, auth_handler: AuthHandler):
        self.user_dao = user_dao
        self.auth_handler = auth_handler

    async def get_by_id(self, user_id: uuid.UUID) -> UserSchema:
        """Получение пользователя по ID"""
        user = await self.user_dao.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with id {user_id} not found")
        user_dict = self.user_dao._model_to_dict(user)
        return UserSchema(**user_dict)

    async def get_list(
        self,
        page: int = 1,
        per_page: int = 20,
        search: Optional[str] = None,
    ) -> tuple[List[UserSchema], int]:
        users_dict, total = await self.user_dao.get_paginated_list(
            page=page,
            per_page=per_page,
            search=search,
        )
        return [UserSchema(**u) for u in users_dict], total

    async def create(self, data: UserCreateRequest) -> UserSchema:
        if await self.user_dao.check_uniques(data.phone, data.email):
            raise UserAlreadyExistsError(
                "User with this email or phone already exists."
            )

        hashed_password = await self.auth_handler.get_password_hash(data.password)
        new_user = UserCreateRequest(
            email=data.email,
            phone=data.phone,
            password=hashed_password,
        )
        new_user_dict = new_user.__dict__
        new_user_dict["password_hash"] = new_user_dict.pop("password")
        new_user_dict["is_active"] = True
        user_dict = await self.user_dao.create(**new_user_dict)
        return UserSchema(**user_dict)

    async def update(self, user_id: uuid.UUID, data: UserUpdateRequest) -> UserSchema:
        user = await self.user_dao.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with id {user_id} not found")

        update_data = data.model_dump(exclude_unset=True, exclude_none=True)
        if not update_data:
            raise UpdateUserNeedFields("Update user needs fields.")

        if (data.phone is not None or data.email is not None) and (
            await self.user_dao.check_uniques_excluding_user(
                phone=data.phone, email=data.email, exclude_user_id=user_id
            )
        ):
            raise UserAlreadyExistsError("Email or phone already taken.")

        for field, value in update_data.items():
            setattr(user, field, value)
        updated_dict = await self.user_dao.update(user)
        return UserSchema(**updated_dict)

    async def delete(self, user_id: uuid.UUID) -> None:
        user = await self.user_dao.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with id {user_id} not found")
        await self.user_dao.delete(user)


def get_users_service() -> UsersService:
    """Фабрика сервиса."""
    return UsersService(user_dao=UserDAO(db_dependency), auth_handler=AuthHandler())
