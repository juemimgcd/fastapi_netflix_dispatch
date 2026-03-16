import enum
import uuid

from sqlalchemy import Enum, ForeignKey, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


class IncidentEventType(str, enum.Enum):
    """
    Timeline 事件类型：
    - COMMENT：用户评论（可选：你也可以不把评论放到事件表里，先只记录状态/指派）
    - STATUS_CHANGED：状态变更
    - ASSIGNED：指派/换处理人
    - CREATED：创建 incident（可选）
    """
    COMMENT = "COMMENT"
    STATUS_CHANGED = "STATUS_CHANGED"
    ASSIGNED = "ASSIGNED"
    CREATED = "CREATED"


class IncidentEvent(Base):
    __tablename__ = "incident_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    type_: Mapped[IncidentEventType] = mapped_column(
        Enum(IncidentEventType, name="incident_event_type"),
        nullable=False,
    )

    # payload 用来放不同类型事件的细节，例如：
    # - STATUS_CHANGED: {"from":"OPEN","to":"TRIAGED"}
    # - ASSIGNED: {"from": null, "to": "<uuid>"}
    # - COMMENT: {"comment_id":"<uuid>"} 或 {"content":"..."}（建议用 comment_id）
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # 一句话摘要，便于列表展示（可选，但通常很好用）
    summary: Mapped[str | None] = mapped_column(String(255), nullable=True)