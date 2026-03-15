"""
Incident 相关的 CRUD（只做数据库层的读写）

原则：
- CRUD 层只关心“怎么查/怎么写”
- 不在这里做 HTTPException（那是 router/service 层的职责）
"""

import uuid
from sqlalchemy import select,or_
from sqlalchemy.ext.asyncio import AsyncSession
from models.incidents import Incident, IncidentStatus


# 创建 incident

async def create_incident(
        db:AsyncSession,
        reporter_id:uuid.UUID,
        title:str,
        description:str | None
):

    incident = Incident(
        reporter_id=reporter_id,
        title=title,
        description=description,
        status=IncidentStatus.OPEN
    )

    db.add(incident)
    await db.commit()
    await db.refresh(incident)
    return incident




async def list_incidents_by_reporter(
        db:AsyncSession,
        reporter_id:uuid.UUID
):
    """
    查询“我创建的 incidents”列表，按创建时间倒序
    """

    stmt = (
        select(Incident)
        .where(Incident.reporter_id == reporter_id)
        .order_by(Incident.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_incident_by_id_and_reporter(
        db:AsyncSession,
        incident_id:uuid.UUID,
        reporter_id:uuid.UUID
):

    """
    获取“我创建的某个 incident”

    如果 incident_id 存在但不是我创建的，这里会返回 None
    （上层 router/service 可以据此返回 403 或 404，按你想要的策略）
    """
    stmt = (
        select(Incident)
        .where(Incident.id == incident_id,Incident.reporter_id == reporter_id)
    )

    result = await db.execute(stmt)

    return result.scalar_one_or_none()


async def get_incident_by_id(db: AsyncSession, incident_id: uuid.UUID) -> Incident | None:
    """
    按 incident_id 获取 incident（不给权限过滤，用于 admin 指派等场景）
    """
    stmt = select(Incident).where(Incident.id == incident_id)
    res = await db.execute(stmt)
    return res.scalar_one_or_none()


async def list_all_incidents(
        db:AsyncSession
):
    """管理员查看全部 incidents"""
    stmt = select(Incident).order_by(Incident.created_at.desc())
    result = await db.execute(stmt)

    return list(result.scalars().all())


async def list_incidents_visible_to_user(
        db:AsyncSession,
        user_id:uuid.UUID
):
    """
    普通用户可见 incidents：
    - 我创建的（reporter_id == user_id）
    - 指派给我的（assignee_id == user_id）
    """
    stmt = (select(Incident)
            .where(or_(Incident.reporter_id == user_id,Incident.assignee_id == user_id))
            .order_by(Incident.created_at.desc())
            )

    result = await db.execute(stmt)

    return list(result.scalars().all())























