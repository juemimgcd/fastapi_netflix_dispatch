import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TeamCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)


class TeamPublic(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


TeamRoleLiteral = Literal["OWNER", "MEMBER"]


class TeamMembershipAddRequest(BaseModel):
    user_id: uuid.UUID
    role: TeamRoleLiteral = "MEMBER"


class TeamMembershipPublic(BaseModel):
    id: uuid.UUID
    team_id: uuid.UUID
    user_id: uuid.UUID
    role: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)