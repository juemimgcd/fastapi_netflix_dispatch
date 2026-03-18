"""
Incident Task 相关 CRUD（只做数据库层读写）

原则：
- 不做 HTTPException
- 不 commit（router commit）
"""

import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from models.incident_tasks import IncidentTask, TaskStatus


async def create_task(
        db: AsyncSession,
        *,
        incident_id: uuid.UUID,
        creator_id: uuid.UUID | None,
        title: str,
        description: str | None,
        assignee_id: uuid.UUID | None,
) -> IncidentTask:
    """
    需要完成的业务/数据目标：
    - 新建 IncidentTask
    - status 默认 TODO
    - db.add(task)
    - 返回 task（不 commit、不 refresh）
    """
    task = IncidentTask(
        incident_id=incident_id,
        creator_id=creator_id,
        title=title,
        description=description,
        assignee_id=assignee_id
    )
    db.add(task)
    return task


async def list_tasks_by_incident(
        db: AsyncSession,
        *,
        incident_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
) -> list[IncidentTask]:
    """
    需要完成的业务/数据目标：
    - 查询某个 incident 下的 task 列表
    - 按 created_at desc
    - 支持分页
    """

    stmt = (
        select(IncidentTask)
        .where(IncidentTask.incident_id == incident_id)
        .order_by(IncidentTask.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    result = await db.execute(stmt)

    task_list = result.scalars().all()

    return list(task_list)


async def list_tasks_assigned_to_user(
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
) -> list[IncidentTask]:
    """
    需要完成的业务/数据目标：
    - 查询指派给某个用户的任务列表（用于“我的任务”）
    - 建议过滤掉 CANCELED（你自己决定）
    """
    stmt = (
        select(IncidentTask)
        .where(IncidentTask.assignee_id == user_id, IncidentTask.status != TaskStatus.CANCELED)
        .order_by(IncidentTask.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    result = await db.execute(stmt)
    assigned_task_list = result.scalars().all()

    return list(assigned_task_list)


async def get_task_by_id(
        db: AsyncSession,
        *,
        task_id: uuid.UUID,
) -> IncidentTask | None:
    """
    需要完成的业务/数据目标：
    - 通过 task_id 获取 task
    """
    stmt = (
        select(IncidentTask)
        .where(IncidentTask.id == task_id)
    )
    result = await db.execute(stmt)

    return result.scalar_one_or_none()


async def update_task_status(
        db: AsyncSession,
        *,
        task: IncidentTask,
        status: TaskStatus,
) -> IncidentTask:
    """
    需要完成的业务/数据目标：
    - 修改 task.status
    - 返回 task（不 commit）
    """
    task.status = status
    return task


async def update_task_assignee(
        db: AsyncSession,
        *,
        task: IncidentTask,
        assignee_id: uuid.UUID | None,
) -> IncidentTask:
    """
    需要完成的业务/数据目标：
    - 修改 task.assignee_id（允许置空）
    - 返回 task（不 commit）
    """
    task.assignee_id = assignee_id
    return task
