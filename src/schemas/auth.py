from pydantic import BaseModel, field_validator

from schemas.helpers import normalize_and_validate_russian_phone


class LoginRequest(BaseModel):
    phone: str
    password: str

    @field_validator("phone", mode="before", check_fields=False)
    @classmethod
    def validate_phone(cls, v):
        return normalize_and_validate_russian_phone(v)


class LoginResponse(BaseModel):
    access_token: str
    session_id: str
