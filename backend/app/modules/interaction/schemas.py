from datetime import datetime

from pydantic import BaseModel, ConfigDict


class InteractionCreate(BaseModel):
    hcp_id: int
    interaction_type: str
    subject: str
    notes: str | None = None
    interaction_date: datetime | None = None


class InteractionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    hcp_id: int
    user_id: int
    interaction_type: str
    subject: str
    notes: str | None
    interaction_date: datetime
    created_at: datetime
    updated_at: datetime