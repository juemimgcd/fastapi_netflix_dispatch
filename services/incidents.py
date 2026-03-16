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


async def get_incident(
        db: AsyncSession,
        *,
        incident_id: uuid.UUID,
) -> Incident | None:
    """
    需要完成的业务目标：
    - 统一通过 incident_id 取 Incident
    - 调用 crud/incidents.get_incident_by_id(db, incident_id)
    - 返回 Incident 或 None

    router 的用法示例：
    - incident = await incident_service.get_incident(...)
    - if not incident: raise HTTPException(404)
    """
    return await incidents.get_incident_by_id(db,incident_id=incident_id)




def can_view_incident(*, user: User, incident: Incident) -> bool:
    """
    需要完成的业务目标（复用你当前规则）：
    - admin 可看全部
    - reporter 可看自己创建的
    - assignee 可看指派给自己的
    """
    is_able_to_view = (
        user.is_superuser
        or incident.assignee_id == user.id
        or incident.reporter_id == user.id
    )
    return is_able_to_view


def can_comment_incident(*, user: User, incident: Incident) -> bool:
    """
    需要完成的业务目标：
    - MVP 阶段：评论权限 = 可见权限（能看就能评）
    - 后续如果要细分（比如只有 reporter/assignee 可评），改这里即可
    """
    return can_view_incident(user=user, incident=incident)


def can_change_status(*, user: User, incident: Incident) -> bool:
    """
    需要完成的业务目标（对齐你现有 router 逻辑）：
    - 只有 admin 或 assignee 才能改状态
    """
    is_able_to_change = (
        user.is_superuser
        or incident.assignee_id == user.id
    )
    return is_able_to_change


def can_assign_incident(*, user: User, incident: Incident) -> bool:
    """
    需要完成的业务目标：
    - 只有 admin（superuser）才能指派
    - incident 参数保留是为了未来扩展（例如 CLOSED 禁止再指派等）
    """
    return user.is_superuser