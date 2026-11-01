from fastapi import HTTPException


class WrongEmailPasswordException(HTTPException):
    pass


class AccountDisabledOrBannedException(HTTPException):
    pass


class WebSocketAuthError(Exception):
    pass


class UserAlreadyExistsError(Exception):
    pass


class UserNotFoundError(Exception):
    pass


class UpdateUserNeedFields(Exception):
    pass
