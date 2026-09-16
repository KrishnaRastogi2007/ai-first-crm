from pydantic import BaseModel, EmailStr , ConfigDict
from datetime import datetime

class UserCreate(BaseModel):
    name:str
    email:EmailStr
    password:str
    role:str = "sales_representative"
    phone:str | None = None

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: str
    role: str
    created_at: datetime
    updated_at: datetime
    phone: str | None
    is_active: bool