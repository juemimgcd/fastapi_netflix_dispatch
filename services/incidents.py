"""
Incident 业务层（service layer）

目的：
- 把“可见性/权限规则”从 routers 里抽出来，避免重复
- 让 router 保持：参数解析 + HTTPException + commit/refresh + response

风格约定（你选择的风格2）：
- service 不抛 HTTPException
- service 返回对象/True/False/None
- router 负责把 None/False 翻译成 HTTPException（404/403/400）
"""

import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from crud import incidents
from models.incidents import Incident
from models.users import User
from crud import incidents, team_memberships


async def get_incident(
        db: AsyncSession,
        *,
        incident_id: uuid.UUID,
) -> Incident | None:
    """
    统一通过 incident_id 取 Incident
    """
    return await incidents.get_incident_by_id(db, incident_id)


async def can_view_incident(
        db: AsyncSession,
        *,
        user: User,
        incident: Incident,
) -> bool:
    """
    可见性规则（升级到 Team RBAC）：
    - admin 可看全部
    - reporter 可看自己创建的
    - assignee 可看指派给自己的
    - team member 可看同 team 的
    """
    if user.is_superuser:
        return True

    if incident.reporter_id == user.id:
        return True

    if incident.assignee_id == user.id:
        return True

    # team member
    membership = await team_memberships.get_membership(
        db,
        team_id=incident.team_id,
        user_id=user.id,
    )
    return membership is not None


async def can_comment_incident(
        db: AsyncSession,
        *,
        user: User,
        incident: Incident,
) -> bool:
    """
    MVP：评论权限 = 可见权限
    """
    return await can_view_incident(db, user=user, incident=incident)


async def can_change_status(
        db: AsyncSession,
        *,
        user: User,
        incident: Incident,
) -> bool:
    """
    状态变更权限：
    - admin
    - assignee

    （team member 不默认拥有改状态权限，避免“路人同组成员改状态”）
    """
    if user.is_superuser:
        return True
    return incident.assignee_id == user.id


async def can_assign_incident(
        db: AsyncSession,
        *,
        user: User,
        incident: Incident,
) -> bool:
    """
    指派权限：
    - MVP：只有 admin 才能指派
    （如果你要升级：team OWNER 也能指派，就在这里查 membership.role）
    """
    return user.is_superuser
