from __future__ import annotations
import uuid
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class NotificationPublic(BaseModel):
    """
    用于前端的通知展示 DTO（只读）
    Pydantic v2 的 model_validate/model_dump 在项目中被使用，保持兼容。
    """
    id: uuid.UUID
    event_type: str
    ref_type: str
    ref_id: uuid.UUID
    message: str
    unread: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)