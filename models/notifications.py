from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # 接收通知的用户
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )

    # 事件类型，例如 INCIDENT_ASSIGNED, COMMENT_ADDED, STATUS_CHANGED 等
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # 关联的资源类型，例如 'incident', 'task', 'comment'
    ref_type: Mapped[str] = mapped_column(String(32), nullable=False)

    # 关联的资源 id（UUID）
    ref_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    # 可显示给用户的消息文本（简短）
    message: Mapped[str] = mapped_column(String(512), nullable=False)

    # 是否未读
    unread: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)



    def __repr__(self) -> str:  # pragma: no cover - convenience
        return f"<Notification id={self.id} user_id={self.user_id} event_type={self.event_type} unread={self.unread}>"