import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class IncidentEventPublic(BaseModel):
    id: uuid.UUID
    incident_id: uuid.UUID
    actor_id: uuid.UUID | None
    type: str = Field(validation_alias="type_")
    payload: dict[str, Any]
    summary: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
