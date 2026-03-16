import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TaskCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    assignee_id: uuid.UUID | None = None  # 可选：创建时就指派


class TaskPublic(BaseModel):
    id: uuid.UUID
    incident_id: uuid.UUID
    creator_id: uuid.UUID | None
    assignee_id: uuid.UUID | None
    title: str
    description: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


TaskStatusLiteral = Literal["TODO", "DONE", "CANCELED"]


class TaskStatusUpdateRequest(BaseModel):
    status: TaskStatusLiteral


class TaskAssignRequest(BaseModel):
    assignee_id: uuid.UUID | None