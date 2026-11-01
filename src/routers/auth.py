from fastapi import APIRouter, Depends, status, HTTPException
from services.auth import (
    get_auth_service,
    AuthService,
    WrongEmailPasswordException,
    AccountDisabledOrBannedException,
)
from schemas.auth import LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
    credentials: LoginRequest, service: AuthService = Depends(get_auth_service)
):
    try:
        return await service.login(creds=credentials)
    except WrongEmailPasswordException as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except AccountDisabledOrBannedException as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


# @router.get("/register_confirm")
# async def register_confirm(
#     token: str, service: UserService = Depends(get_users_service)
# ):
#     """Подтверждение email по токену из письма."""
#     await service.confirm_user(token=token)
#     return {"message": "Электронная почта подтверждена"}


# @router.get("/logout")
# async def logout(
#     current_user: UserMeResponse = Depends(get_current_user),
#     service: UserService = Depends(get_users_service),
# ):
#     return await service.logout_user(user=current_user)
