from datetime import datetime
from enum import Enum

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


class UserRole(str, Enum):
    ADMIN = "admin"
    SALES_MANAGER = "sales_manager"
    FIELD_REPRESENTATIVE = "field_representative"
    COMPLIANCE_OFFICER = "compliance_officer"

def validate_password_rules(password: str) -> str:
    if not any(char.isupper() for char in password):
        raise ValueError("Password Must Contain At Least One UpperCase Letter")

    if not any(char.islower() for char in password):
        raise ValueError("Password Must Contain At Least One LowerCase Letter")

    if not any(char.isdigit() for char in password):
        raise ValueError("Password Must Contain At Least One Number")

    if not any(not char.isalnum() for char in password):
        raise ValueError("Password Must Contain At Least One Special Character")

    return password



class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str=Field(min_length=8)
    phone: str | None = None

    @field_validator("password")
    @classmethod

    def validate_password(cls,password :str) ->str:
     return validate_password_rules(password)



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

class UserRoleUpdate(BaseModel):
    role:UserRole


class UserUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password:str =Field(min_length=1)
    new_password :str = Field(min_length=8,max_length=80)
    confirm_password:str =Field(min_length=1)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls,password: str) ->str:
        return validate_password_rules(password)

    @model_validator(mode = "after")
    def password_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("New Password And Confirm Password Do Not Match")

        if self.current_password == self.new_password:
            raise ValueError("New Password Must Be Different From Current Password")
        return self

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str