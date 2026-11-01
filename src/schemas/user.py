import uuid
import datetime
from typing import Annotated, Optional

from pydantic import BaseModel, Field, StringConstraints, field_validator

from schemas.helpers import normalize_and_validate_russian_phone


class UserSchema(BaseModel):
    id: uuid.UUID
    phone: str
    email: Optional[str] = None

    is_active: bool
    is_banned: bool
    is_superuser: bool
    is_verified: bool

    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {"from_attributes": True}


class UserPaginatedResponse(BaseModel):
    total: int
    page: int
    per_page: int
    items: list[UserSchema]


class UserCreateRequest(BaseModel):
    phone: Optional[str] = Field(..., example="+79999999999")
    email: Optional[str] = Field(None, min_length=5, example="user@example.com")
    password: Annotated[str, StringConstraints(min_length=3, max_length=255)]

    @field_validator("phone", mode="before", check_fields=False)
    @classmethod
    def validate_phone(cls, v):
        return normalize_and_validate_russian_phone(v)


class UserUpdateRequest(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None

    is_active: Optional[bool] = None
    is_banned: Optional[bool] = None
    is_superuser: Optional[bool] = None
    is_verified: Optional[bool] = None

    @field_validator("phone", mode="before", check_fields=False)
    @classmethod
    def validate_phone(cls, v):
        return normalize_and_validate_russian_phone(v)


class UserRegisterResponse(BaseModel):
    user: UserSchema
    access_token: str
    session_id: str
