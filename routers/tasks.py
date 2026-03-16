import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from services.incidents import can_view_incident
from conf.db_conf import get_database
from crud import incidents
from crud import tasks
from models.incident_tasks import TaskStatus
from models.users import User
from schemas.tasks import (
    TaskAssignRequest,
    TaskCreateRequest,
    TaskPublic,
    TaskStatusUpdateRequest,
)
from utils.auth import get_current_user
from utils.response import success_response

# 注意：你已有“incident 可见性规则”，这里建议继续复用：
# - admin / reporter / assignee 可见一个 incident
# 为了不引入 Step10 的瘦身，我们先在 router 里直接写判断或调用 service.can_view_incident

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/mine")
async def list_my_tasks(
        limit: int = 50,
        offset: int = 0,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database),
):
    """
    需要完成的业务目标：
    - 列出“指派给我”的任务列表（不需要 incident 可见性判断）
    - 调用 task_crud.list_tasks_assigned_to_user
    - 参数保护：limit 1~100, offset>=0
    - 返success_response(data=[TaskPublic...])
    """
    task_list = await tasks.list_tasks_assigned_to_user(
        db,
        user_id=user.id,
        limit=limit,
        offset=offset
    )

    data = [TaskPublic.model_validate(u) for u in task_list]

    return success_response(data=data)



@router.post("/incident/{incident_id}")
async def create_task_for_incident(
        incident_id: uuid.UUID,
        payload: TaskCreateRequest,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database),
):
    """
    需要完成的业务目标：
    1) incident 必须存在（不存在 -> 404）
    2) 权限：只有能查看该 incident 的人（admin/reporter/assignee）才能在其下创建 task
    3) 调用 crud.create_task（creator_id=user.id）
    4) commit + refresh
    5) 返回 TaskPublic
    """
    incident = await incidents.get_incident_by_id(db,incident_id=incident_id)
    if not incident:
        raise HTTPException(status_code=404,detail="Incident not found")

    if can_view_incident(user=user,incident=incident):
        task = tasks.create_task(
            db,incident_id=incident_id,
            creator_id=user.id,
            title=payload.title,
            description=payload.description,
            assignee_id=payload.assignee_id
        )
        await db.commit()
        await db.refresh(task)

        return success_response(data=TaskPublic.model_validate(task))

    else:
        raise HTTPException(status_code=403, detail="low rights")





@router.get("/incident/{incident_id}")
async def list_tasks_for_incident(
        incident_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database),
):
    """
    需要完成的业务目标：
    1) incident 必须存在（不存在 -> 404）
    2) 权限：incident 可见性（admin/reporter/assignee）
    3) 调用 crud.list_tasks_by_incident
    4) 返回 TaskPublic 列表
    """
    incident = await incidents.get_incident_by_id(db,incident_id=incident_id)
    if not incident:
        raise HTTPException(status_code=404,detail="Incident not found")

    if can_view_incident(user=user,incident=incident):
        task_list = await tasks.list_tasks_by_incident(db,incident_id=incident_id,limit=limit,offset=offset)

        data = [TaskPublic.model_validate(u) for u in task_list]
        return success_response(data=data)
    else:
        raise HTTPException(status_code=403, detail="low rights")




@router.patch("/{task_id}/status")
async def update_task_status(
        task_id: uuid.UUID,
        payload: TaskStatusUpdateRequest,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database),
):
    """
    需要完成的业务目标：
    1) task 必须存在（不存在 -> 404）
    2) 找到 task 所属 incident，并做 incident 可见性校验（admin/reporter/assignee）
    3) 状态流转规则（MVP）：
       - TODO -> DONE/CANCELED
       - DONE -> （不允许再变） 或允许回 TODO（你决定）
       - CANCELED -> （不允许再变）
    4) 调用 crud.update_task_status
    5) commit + refresh
    """
    task = await tasks.get_task_by_id(db,task_id=task_id)
    if not task:
        raise HTTPException(status_code=404,detail="Incident not found")
    incident = await incidents.get_incident_by_id(db,task.incident_id)

    allowed_transformation = {
        "TODO":{"DONE","CANCELED"},
        "DONE":set(),
        "CANCELED":set()
    }
    old_status = str(incident.status)
    new_status = TaskStatus(payload.status)
    if not can_view_incident(user=user,incident=incident):
        raise HTTPException(status_code=403,detail="Low rights")
    if new_status not in allowed_transformation.get(old_status,set()):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status transition:{old_status} -> {new_status}",
        )

    transferred_task = await tasks.update_task_status(db,task=task,status=new_status)
    await db.commit()
    await db.refresh(transferred_task)

    return success_response(data=TaskPublic.model_validate(transferred_task))


@router.patch("/{task_id}/assign")
async def assign_task(
        task_id: uuid.UUID,
        payload: TaskAssignRequest,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database),
):
    """
    需要完成的业务目标：
    1) task 必须存在（不存在 -> 404）
    2) incident 可见性校验（admin/reporter/assignee）
    3) 更新 assignee_id（允许置空）
    4) commit + refresh
    """
    task = await tasks.get_task_by_id(db,task_id=task_id)
    if not task:
        raise HTTPException(status_code=404,detail="Incident not found")

    incident = await incidents.get_incident_by_id(db,task.incident_id)
    if not can_view_incident(user=user,incident=incident):
        raise HTTPException(status_code=403,detail="Low rights")

    transferred_task = tasks.update_task_assignee(db,task=task,assignee_id=payload.assignee_id)
    await db.commit()
    await db.refresh(transferred_task)

    return success_response(data=TaskPublic.model_validate(transferred_task))
















