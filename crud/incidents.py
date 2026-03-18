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
from models.team_memberships import TeamMembership


# 创建 incident

async def create_incident(
        db:AsyncSession,
        reporter_id:uuid.UUID,
        title:str,
        description:str | None,
        team_id: uuid.UUID,
):

    incident = Incident(
        reporter_id=reporter_id,
        title=title,
        description=description,
        status=IncidentStatus.OPEN,
        team_id=team_id,
    )

    db.add(incident)
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
    my_team_ids_subq = (
        select(TeamMembership.team_id)
        .where(TeamMembership.user_id == user_id)
        .subquery()
    )

    stmt = (
        select(Incident)
        .where(
            or_(
                Incident.reporter_id == user_id,
                Incident.assignee_id == user_id,
                Incident.team_id.in_(select(my_team_ids_subq.c.team_id)),
                )
        )
        .order_by(Incident.created_at.desc())
    )

    res = await db.execute(stmt)
    return list(res.scalars().all())


async def search_incidents(
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        is_admin: bool,
        q: str | None = None,
        status: str | None = None,
        team_id: uuid.UUID | None = None,
        assignee_id: uuid.UUID | None = None,
        reporter_id: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
) -> list[Incident]:
    """
    对 incidents 做搜索 + 过滤，并内置权限（非 admin 只能搜到可见范围）。

    可见性（非 admin）：
    - reporter_id == user_id
    - assignee_id == user_id
    - incident.team_id in (user's teams)
    """
    stmt = select(Incident)

    if not is_admin:
        my_team_ids = (
            select(TeamMembership.team_id).where(TeamMembership.user_id == user_id)
        )


        stmt = stmt.where(
            or_(
                Incident.reporter_id == user_id,
                Incident.assignee_id == user_id,
                Incident.team_id.in_(my_team_ids)
            )
        )

    if status is not None:
        stmt = stmt.where(Incident.status == status)

    if team_id is not None:
        stmt = stmt.where(Incident.team_id == team_id)

    if assignee_id is not None:
        stmt = stmt.where(Incident.assignee_id == assignee_id)

    if reporter_id is not None:
        stmt = stmt.where(Incident.reporter_id == reporter_id)

    if q:
        # 简易 ILIKE 模糊匹配（Postgres）
        like = f"%{q}%"
        stmt = stmt.where(or_(Incident.title.ilike(like), Incident.description.ilike(like)))

    stmt = (
        stmt.order_by(Incident.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    res = await db.execute(stmt)
    return list(res.scalars().all())

































