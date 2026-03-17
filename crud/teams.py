import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.teams import Team


async def create_team(db: AsyncSession, *, name: str) -> Team:

    team = Team(
        name=name
    )
    db.add(team)
    return team



async def get_team_by_id(db: AsyncSession, *, team_id: uuid.UUID) -> Team | None:
    stmt = (
        select(Team)
        .where(Team.id == team_id)
    )

    result = await db.execute(stmt)

    return result.scalar_one_or_none()



async def get_team_by_name(db: AsyncSession, *, name: str) -> Team | None:

    stmt = (
        select(Team)
        .where(Team.name == name)
    )
    res = await db.execute(stmt)

    return res.scalar_one_or_none()




async def list_teams(db: AsyncSession, *, limit: int = 50, offset: int = 0) -> list[Team]:

    stmt = (
        select(Team)
        .limit(limit)
        .offset(offset)
    )

    result = await db.execute(stmt)

    team_list = result.scalars().all()

    return list(team_list)

