import uuid
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict


IncidentStatus = Literal["OPEN", "TRIAGED", "CLOSED"]


class IncidentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None


class IncidentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    status: IncidentStatus | None = None  # 允许 assignee/admin 更新


class IncidentAssignRequest(BaseModel):
    assignee_id: uuid.UUID


class IncidentPublic(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    status: str
    reporter_id: uuid.UUID
    assignee_id: uuid.UUID | None

    model_config = ConfigDict(from_attributes=True)