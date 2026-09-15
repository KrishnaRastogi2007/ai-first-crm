"""
API mein data ka structure/validation.

Frontend
   ↓
Pydantic Schema
   ↓
FastAPI
SCHEMA = API data
"""
from pydantic import BaseModel , ConfigDict

class HCPCreate(BaseModel):
    name:str
    specialty:str
    email:str | None = None
    phone:str | None = None
    organization:str | None = None

class HCPResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id:int
    name:str
    specialty:str
    email:str | None = None
    phone:str | None = None
    organization:str | None = None