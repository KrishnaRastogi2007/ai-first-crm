from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: str | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: EmailStr
    role: str
    created_at: datetime
    updated_at: datetime
    phone: str | None
    is_active: bool


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class PaginatedUserResponse(BaseModel):
    items: list[UserResponse]
    page: int
    limit: int
    total: int
    pages: int