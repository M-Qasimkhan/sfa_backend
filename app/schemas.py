from datetime import date, datetime
from typing import Any
from pydantic import BaseModel, EmailStr, field_validator

from app.models import Role


class UserCreate(BaseModel):
    name: str
    phone: str | None = None
    cnic: str | None = None
    email: EmailStr
    area: str | None = None
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


class UserUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    cnic: str | None = None
    email: EmailStr | None = None
    area: str | None = None
    image: str | None = None

    @field_validator("image", mode="before")
    @classmethod
    def normalize_image(cls, value: Any) -> Any:
        if value == "":
            return None
        return value


class AssignUserRequest(BaseModel):
    child_id: int
    parent_id: int


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


class CategoryCreate(BaseModel):
    name: str
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Category name is required")
        return value


class CategoryUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None


class CategoryOut(BaseModel):
    id: int
    name: str
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class ProductCreate(BaseModel):
    category_id: int
    name: str
    sku: str
    price: float = 0
    stock: int = 0
    description: str | None = None
    image: str | None = None
    is_active: bool = True

    @field_validator("name", "sku")
    @classmethod
    def normalize_string(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field is required")
        return value


class ProductUpdate(BaseModel):
    category_id: int | None = None
    name: str | None = None
    sku: str | None = None
    price: float | None = None
    stock: int | None = None
    description: str | None = None
    image: str | None = None
    is_active: bool | None = None


class ProductOut(BaseModel):
    id: int
    category_id: int
    name: str
    sku: str
    price: float
    stock: int
    description: str | None = None
    image: str | None = None
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None
    category: CategoryOut | None = None

    model_config = {"from_attributes": True}


class UserOut(BaseModel):
    id: int
    name: str
    phone: str | None = None
    cnic: str | None = None
    email: str
    area: str | None = None
    zsm_id: int | None = None
    tsm_id: int | None = None
    asm_id: int | None = None
    image: str | None = None
    role: Role
    is_active: bool

    model_config = {"from_attributes": True}


class AttendanceCheckIn(BaseModel):
    date: date
    check_in: datetime
    check_in_location: str


class AttendanceBreakStart(BaseModel):
    break_start: datetime


class AttendanceBreakEnd(BaseModel):
    break_end: datetime


class AttendanceCheckout(BaseModel):
    check_out: datetime
    check_out_location: str


class AttendanceOut(BaseModel):
    id: int
    user_id: int
    date: date
    day: int
    month: int
    year: int
    check_in: datetime | None = None
    check_in_location: str | None = None
    break_start: datetime | None = None
    break_end: datetime | None = None
    check_out: datetime | None = None
    check_out_location: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class LeaveCreate(BaseModel):
    category: str
    start_date: date
    end_date: date
    reason: str
    evidence_image: str | None = None


class LeaveOut(BaseModel):
    id: int
    user_id: int
    category: str
    start_date: date
    end_date: date
    reason: str
    evidence_image: str | None = None
    status: bool | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class LeaveStatusUpdate(BaseModel):
    status: bool


class AuthResponse(BaseModel):
    message: str
    user: UserOut
    session_key: str
