from pydantic import BaseModel
from datetime import datetime

class UserCreate(BaseModel):
    name:str
    email:str
    password:str
    role:str = "sales_representative"
    phone:str | None = None

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    created_at: datetime
    updated_at: datetime
    phone: str | None
    is_active: bool