import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status, Query
from fastapi.exceptions import HTTPException

from dependencies.auth import get_current_user
from services.auth import AuthService, get_auth_service
from services.user import (
    UsersService,
    UserAlreadyExistsError,
    UserNotFoundError,
    UpdateUserNeedFields,
    get_users_service,
)
from schemas.user import (
    UserCreateRequest,
    UserSchema,
    UserPaginatedResponse,
    UserUpdateRequest,
    UserRegisterResponse,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "/register",
    response_model=UserRegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    data: UserCreateRequest,
    users_service: UsersService = Depends(get_users_service),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserRegisterResponse:
    try:
        new_user = await users_service.create(data)
        access_token, session_id = await auth_service.create_and_store_access_token(
            new_user.id
        )
        return UserRegisterResponse(
            user=new_user, access_token=access_token, session_id=session_id
        )
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/me", response_model=UserSchema)
async def me(
    current_user: Annotated[UserSchema, Depends(get_current_user)],
) -> UserSchema:
    return current_user


@router.get("/", response_model=UserPaginatedResponse)
async def get_users(
    current_user: Annotated[UserSchema, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    users_service: UsersService = Depends(get_users_service),
) -> UserPaginatedResponse:
    items, total = await users_service.get_list(page, per_page, search)
    return UserPaginatedResponse(
        total=total,
        page=page,
        per_page=per_page,
        users=items,
    )


@router.get("/{id}", response_model=UserSchema)
async def get_user(
    current_user: Annotated[UserSchema, Depends(get_current_user)],
    id: uuid.UUID,
    users_service: UsersService = Depends(get_users_service),
) -> UserSchema:
    if current_user.id != id and not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав.")
    try:
        return await users_service.get_by_id(id)
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/", response_model=UserSchema)
async def create_user(
    data: UserCreateRequest,
    users_service: UsersService = Depends(get_users_service),
) -> UserSchema:
    try:
        return await users_service.create(data)
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.patch("/{id}", response_model=UserSchema)
async def update_user(
    current_user: Annotated[UserSchema, Depends(get_current_user)],
    id: uuid.UUID,
    data: UserUpdateRequest,
    users_service: UsersService = Depends(get_users_service),
) -> UserSchema:
    is_self = current_user.id == id
    if not is_self and not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав.")
    privileged_fields = {"is_active", "is_banned", "is_superuser", "is_verified"}

    if not current_user.is_superuser and privileged_fields.intersection(
        data.model_fields_set
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав.")

    try:
        return await users_service.update(user_id=id, data=data)
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except UpdateUserNeedFields as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{id}", response_model=None)
async def delete_user(
    current_user: Annotated[UserSchema, Depends(get_current_user)],
    id: uuid.UUID,
    users_service: UsersService = Depends(get_users_service),
) -> None:
    if current_user.id != id and not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нет прав.")
    try:
        return await users_service.delete(id)
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
