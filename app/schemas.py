from datetime import datetime
from typing import Any
from pydantic import BaseModel, EmailStr, field_validator

from app.models import Role


class UserCreate(BaseModel):
    name: str
    phone: str | None = None
    cnic: str | None = None
    email: EmailStr
    password: str
    image: str | None = None
    role: str | Role = Role.SR

    @field_validator("role", mode="before")
    @classmethod
    def normalize_role(cls, value: Any) -> Any:
        if isinstance(value, str):
            normalized = value.strip().upper()
            if normalized in {role.value for role in Role}:
                return normalized
        return value

    @field_validator("image", mode="before")
    @classmethod
    def normalize_image(cls, value: Any) -> Any:
        if value == "":
            return None
        return value


class LoginRequest(BaseModel):
    email: str
    password: str


class ShopCreate(BaseModel):
    name: str
    address: str | None = None
    phone: str | None = None
    image: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class ShopOut(BaseModel):
    id: int
    name: str
    address: str | None = None
    phone: str | None = None
    image: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    created_by_id: int | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class UserOut(BaseModel):
    id: int
    name: str
    phone: str | None = None
    cnic: str | None = None
    email: str
    image: str | None = None
    role: Role
    is_active: bool

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    message: str
    user: UserOut
