from pydantic import BaseModel, ConfigDict


class HCPCreate(BaseModel):
    name: str
    specialty: str
    email: str | None = None
    phone: str | None = None
    organization: str | None = None


class HCPResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    specialty: str
    email: str | None = None
    phone: str | None = None
    organization: str | None = None
    assigned_to: int | None = None


class PaginatedHCPResponse(BaseModel):
    items: list[HCPResponse]
    page: int
    limit: int
    total: int
    pages: int


class HCPAssignment(BaseModel):
    assigned_to: int| None
    