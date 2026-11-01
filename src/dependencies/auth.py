import uuid
from typing import Annotated

from fastapi import HTTPException, Depends
from starlette import status
from starlette.requests import Request

from services.auth import AuthService, get_auth_service
from services.user import UsersService, get_users_service
from handlers.auth import AuthHandler
from schemas.user import UserResponse
from exceptions import UserNotFoundError


async def get_token_from_headers(request: Request) -> str:
    token = request.headers.get("Authorization")
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is missing"
        )
    return token


async def get_current_user(
    token: Annotated[str, Depends(get_token_from_headers)],
    auth_handler: AuthHandler = Depends(AuthHandler),
    auth_service: AuthService = Depends(get_auth_service),
    users_service: UsersService = Depends(get_users_service),
) -> UserResponse:
    user, session_id = await _authenticate_access_token(
        token, auth_handler, auth_service, users_service
    )
    return UserResponse(
        id=user.id,
        email=user.email,
        phone=user.phone,
        is_active=user.is_active,
        is_banned=user.is_banned,
        is_superuser=user.is_superuser,
        is_verified=user.is_verified,
        created_at=user.created_at,
        updated_at=user.updated_at,
        session_id=session_id,
        # roles=user["roles"],
    )


async def _authenticate_access_token(
    token: str,
    auth_handler: AuthHandler,
    auth_service: AuthService,
    users_service: UsersService,
) -> tuple[UserResponse, str]:
    decoded_token = await auth_handler.decode_access_token(token=token)
    user_id_value = decoded_token.get("user_id")
    session_id = decoded_token.get("session_id")

    if decoded_token.get("sub") != user_id_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is invalid"
        )

    try:
        user_id = uuid.UUID(user_id_value)
    except TypeError, ValueError, AttributeError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is invalid"
        )

    if not isinstance(session_id, str) or not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is invalid"
        )

    stored_token = await auth_service.get_access_token(user_id, session_id)
    if stored_token != token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is invalid"
        )

    try:
        user = await users_service.get_by_id(user_id)
    except UserNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        ) from error

    if not user.is_active or user.is_banned:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled or banned",
        )

    return user, session_id
