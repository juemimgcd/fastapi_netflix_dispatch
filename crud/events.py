"""
Incident Timeline(Event) 相关 CRUD
原则：
- 只做数据库读写
- 不做 HTTPException
- 不 commit（router 层 commit）
"""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.incident_events import IncidentEvent, IncidentEventType


async def create_event(
        db: AsyncSession,
        *,
        incident_id: uuid.UUID,
        actor_id: uuid.UUID | None,
        type_: IncidentEventType,
        payload: dict,
        summary: str | None = None,
) -> IncidentEvent:
    """
    需要完成的业务/数据目标：
    - 新建 IncidentEvent
    - db.add(event)
    - 返回 event（不 commit，不 refresh）
    """
    event = IncidentEvent(
        incident_id=incident_id,
        actor_id=actor_id,
        type_=type_,
        payload=payload,
        summary=summary
    )
    db.add(event)
    return event



async def list_events_by_incident(
        db: AsyncSession,
        *,
        incident_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
) -> list[IncidentEvent]:
    """
    需要完成的业务/数据目标：
    - 查询某个 incident 下的事件流（按 created_at desc）
    - 支持分页 limit/offset
    """
    stmt = (
        select(IncidentEvent)
        .where(IncidentEvent.incident_id == incident_id)
        .order_by(IncidentEvent.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    result = await db.execute(stmt)

    event_list = result.scalars().all()

    return list(event_list)
