import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CommentCreateRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class CommentPublic(BaseModel):
    id: uuid.UUID
    incident_id: uuid.UUID
    author_id: uuid.UUID
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)