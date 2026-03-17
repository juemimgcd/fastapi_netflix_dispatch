import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from crud import team_memberships as membership_crud
from models.users import User


async def is_team_member(
        db: AsyncSession,
        *,
        user: User,
        team_id: uuid.UUID,
) -> bool:
    if user.is_superuser:
        return True
    membership = await membership_crud.get_membership(db, team_id=team_id, user_id=user.id)
    return membership is not None