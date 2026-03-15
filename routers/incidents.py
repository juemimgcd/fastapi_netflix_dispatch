"""Incident 路由

MVP incident + Step6 权限可见性 + Step7 状态流转

路由约定：
- POST   /api/v1/incidents                 创建（登录）
- GET    /api/v1/incidents/mine            我创建的列表（登录）
- GET    /api/v1/incidents                 我可见的列表（登录；admin=全部）
- GET    /api/v1/incidents/{incident_id}   详情（登录；reporter/assignee/admin 可见）
- PATCH  /api/v1/incidents/{incident_id}/status  更新状态（登录；assignee/admin）
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from conf.db_conf import get_database
from crud import incidents
from models.incidents import IncidentStatus
from models.users import User
from schemas.incidents import (
    IncidentCreateRequest,
    IncidentPublic,
    IncidentStatusUpdateRequest,
)
from utils.auth import get_current_user
from utils.response import success_response

router = APIRouter(prefix="/incidents", tags=["incidents"])

@router.post("")
async def create_incident(
    payload: IncidentCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database),
):
    """创建 incident（reporter_id 强制使用当前用户 id）"""
    incident = await incidents.create_incident(
        db,
        reporter_id=user.id,
        title=payload.title,
        description=payload.description,
    )

    # 统一在 router 层提交事务
    await db.commit()
    await db.refresh(incident)

    data = IncidentPublic.model_validate(incident)
    return success_response(data=data)

@router.get("/mine")
async def list_my_incidents(
    db: AsyncSession = Depends(get_database),
    user: User = Depends(get_current_user),
):
    """查询“我创建的 incident 列表"""  #按创建时间倒序"""
    incident_list = await incidents.list_incidents_by_reporter(db, reporter_id=user.id)
    data = [IncidentPublic.model_validate(info) for info in incident_list]
    return success_response(data=data)

@router.get("")
async def list_incidents(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database),
):
    """列表可见性规则（Step 6）：admin 全部；普通用户=我创建 + 指派给我"""
    if user.is_superuser:
        incident_list = await incidents.list_all_incidents(db)
    else:
        incident_list = await incidents.list_incidents_visible_to_user(db, user_id=user.id)

    data = [IncidentPublic.model_validate(u) for u in incident_list]
    return success_response(data=data)

@router.get("/{incident_id}")
async def get_incident_detail(
    incident_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database),
):
    """详情可见性规则（Step 6）：reporter / assignee / admin 可看"""
    incident = await incidents.get_incident_by_id(db, incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    is_able_to_view = (
        user.is_superuser
        or incident.reporter_id == user.id
        or incident.assignee_id == user.id
    )

    if not is_able_to_view:
        # 这里按你的策略：403（明确无权限）。如果想防止信息泄露也可返回 404。
        raise HTTPException(status_code=403, detail="low rights")

    data = IncidentPublic.model_validate(incident)
    return success_response(data=data)

@router.patch("/{incident_id}/status")
async def update_incident_status(
    incident_id: uuid.UUID,
    payload: IncidentStatusUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database),
):
    incident = await incidents.get_incident_by_id(db, incident_id)

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    if not (user.is_superuser or incident.assignee_id == user.id):
        raise HTTPException(
            status_code=403,
            detail="Only assignee or admin is supposed to change the status",
        )

    current_status = str(incident.status)
    target = payload.status
    allowed_transitions = {
        "OPEN": {"TRIAGED"},
        "TRIAGED": {"CLOSED"},
        "CLOSED": set(),
    }

    if target == current_status:
        data = IncidentPublic.model_validate(incident)
        return success_response(data=data)

    if target not in allowed_transitions.get(current_status, set()):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status transition:{current_status} -> {target}",
        )

    incident.status = IncidentStatus(target)

    await db.commit()
    await db.refresh(incident)

    data = IncidentPublic.model_validate(incident)
    return success_response(data=data)