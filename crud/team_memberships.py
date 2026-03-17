import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.team_memberships import TeamMembership, TeamRole


async def add_membership(
        db: AsyncSession,
        *,
        team_id: uuid.UUID,
        user_id: uuid.UUID,
        role: TeamRole,
) -> TeamMembership:
    """
    - 新建 TeamMembership(team_id, user_id, role)
    - 注意唯一约束 team_id+user_id：重复要在 router/service 处理（或捕获 IntegrityError）
    """
    membership = TeamMembership(
        team_id=team_id,
        user_id=user_id,
        role=role
    )
    db.add(membership)
    return membership



async def get_membership(
        db: AsyncSession,
        *,
        team_id: uuid.UUID,
        user_id: uuid.UUID,
) -> TeamMembership | None:

    stmt = (
        select(TeamMembership)
        .where(TeamMembership.team_id == team_id,TeamMembership.user_id == user_id)

    )

    res = await db.execute(stmt)

    return res.scalar_one_or_none()




async def list_team_memberships(
        db: AsyncSession,
        *,
        team_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
) -> list[TeamMembership]:

    stmt = (
        select(TeamMembership)
        .where(TeamMembership.team_id == team_id)
        .limit(limit)
        .offset(offset)
    )
    res = await db.execute(stmt)

    membership_list = res.scalars().all()

    return list(membership_list)






