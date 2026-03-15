"""
Incident 路由（MVP-1）

只实现三个接口：
- POST   /api/v1/incidents        创建事件（登录）
- GET    /api/v1/incidents/list        查看“我创建的事件”列表（登录）
- GET    /api/v1/incidents/{id}   查看“我创建的事件”详情（登录）

权限策略（MVP-1）：
- 只能访问 reporter_id == 当前用户 id 的 incidents
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from conf.db_conf import get_database
from crud import incidents
from models.users import User
from models.incidents import IncidentStatus
from schemas.incidents import IncidentCreateRequest, IncidentPublic,IncidentStatusUpdateRequest
from utils.auth import get_current_user
from utils.response import success_response

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.post("")
async def create_incident(
        payload: IncidentCreateRequest,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database)
):
    """
    创建 incident：
    - reporter_id 永远使用当前登录用户的 id（不允许前端传，防止伪造）
    """
    incident = await incidents.create_incident(db,
                                               reporter_id=user.id,
                                               title=payload.title,
                                               description=payload.description)

    data = IncidentPublic.model_validate(incident)
    return success_response(data=data)


@router.get("")
async def list_my_incidents(
        db: AsyncSession = Depends(get_database),
        user: User = Depends(get_current_user)
):
    """
    查询“我创建的 incident 列表”
    """
    incident_list = await incidents.list_incidents_by_reporter(
        db,
        reporter_id=user.id
    )

    data = [IncidentPublic.model_validate(info) for info in incident_list]

    return success_response(data=data)


@router.get("/{incident_id}")
async def get_my_incident_detail(
        incident_id: uuid.UUID,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database)
):
    """
    查询“我创建的 incident 详情”
    如果查不到，一律返回 404（避免泄露他人 incident 是否存在）
    """

    incident = await incidents.get_incident_by_id_and_reporter(
        db,
        incident_id=incident_id,
        reporter_id=user.id
    )
    if not incident:
        raise HTTPException(status_code=404,detail="Incident not found")

    data = IncidentPublic.model_validate(incident)

    return success_response(data=data)


@router.get("{incident_id}")
async def get_incident_detail(
        incident_id:uuid.UUID,
        user:User = Depends(get_current_user),
        db:AsyncSession = Depends(get_database)
):
    """
    详情可见性规则（Step 6）：
    - reporter / assignee / admin 可以看
    """
    incident = await incidents.get_incident_by_id(db,incident_id)

    if not incident:
        raise HTTPException(status_code=404,detail="Incident not found")

    is_able_to_view = (
        user.is_superuser
        or incident.reporter_id == user.id
        or incident.assignee_id == user.id
    )

    if not is_able_to_view:
        raise HTTPException(status_code=403,detail="low rights")

    data = IncidentPublic.model_validate(incident)

    return success_response(data=data)


@router.get("")
async def list_incidents(
        user:User = Depends(get_current_user),
        db:AsyncSession = Depends(get_database)
):
    """
    列表可见性规则（Step 6）：
    - admin：看全部
    - 普通用户：看“我创建的 + 指派给我的”
    """
    if user.is_superuser:
        incident_list = await incidents.list_all_incidents(db)
    else:
        incident_list = await incidents.list_incidents_visible_to_user(db,user_id=user.id)

    data = [IncidentPublic.model_validate(u) for u in incident_list]
    return success_response(data=data)


@router.patch("/{incident_id}/status")
async def update_incident_status(
        incident_id:uuid.UUID,
        payload:IncidentStatusUpdateRequest,
        user:User = Depends(get_current_user),
        db:AsyncSession = Depends(get_database)
):
    incident = await incidents.get_incident_by_id(db,incident_id)

    if not incident:
        raise HTTPException(status_code=404,detail="Incident not found")

    if not (user.is_superuser or incident.assignee_id == user.id):
        raise HTTPException(status_code=403,detail="Only assignee or admin is supposed to change the status")

    current_status = str(incident.status)
    target = payload.status
    allowed_transitions = {
        "OPEN":{"TRIAGED"},
        "TRIAGED":{"CLOSED"},
        "CLOSED":set()
    }

    if target == current_status:
        data = IncidentPublic.model_validate(incident)
        return success_response(data=data)

    if target not in allowed_transitions.get(current_status,set()):
        raise HTTPException(status_code=400,
                            detail=f"Invalid status transition:{current_status} -> {target}"
                            )
    incident.status = IncidentStatus(target)

    await db.commit()
    await db.refresh(incident)

    data = IncidentPublic.model_validate(incident)

    return success_response(data=data)


























