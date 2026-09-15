from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FollowUpCreate(BaseModel):
    interaction_id: int
    assigned_to: int
    due_date: datetime
    status: str = "pending"
    notes: str | None = None


class FollowUpResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    interaction_id: int
    assigned_to: int
    due_date: datetime
    status: str
    notes: str | None
    created_at: datetime
    updated_at: datetime