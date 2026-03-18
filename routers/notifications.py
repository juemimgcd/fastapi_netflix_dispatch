"""
Notifications HTTP 路由（router 层）——你实现函数体即可。下面仅给出路由、签名与详细注释（帮助你快速实现）。
- router 应在 router.api_router 中 include（你来把 include_router 放到 routers/router.py）
- router 内的函数需负责 commit/refresh（或按你项目约定）
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from crud import notifications
from conf.db_conf import get_database
from models.users import User
from schemas.notifications import NotificationPublic
from utils.auth import get_current_user
from utils.response import success_response

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
async def get_my_notifications(
        unread: bool | None = None,
        limit: int = 50,
        offset: int = 0,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database),
):
    """
    返回当前登录用户的通知列表（分页）。
    业务/实现提示：
    - 调用 crud.list_notifications(db, user_id=user.id, unread=unread, limit=limit, offset=offset)
    - 把 ORM 对象转换为 NotificationPublic.model_validate(x).model_dump() 或直接 model_validate 后返回
    - 使用 success_response(data=...) 返回
    """

    notes = await notifications.list_notifications(
        db,
        user_id=user.id,
        unread=unread,
        limit=limit,
        offset=offset
    )

    data = [NotificationPublic.model_validate(u) for u in notes]

    return success_response(data=data)









@router.post("/{notification_id}/read")
async def set_notification_read(
        notification_id: uuid.UUID,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database),
):
    """
    标记单条通知为已读。
    业务/实现提示：
    - 可先校验 notification 属于当前用户（或让 CRUD 层只更新 user_id 对应项）
    - 调用 crud.mark_notification_read(db, notification_id)
    - await db.commit()
    - 返回 success_response()
    """
    note = await notifications.get_notification_by_id(
        db,
        notification_id=notification_id,
    )
    if note.user_id != user.id:
        raise HTTPException(status_code=404,detail="Note not found")

    await notifications.mark_notification_read(
        db,
        notification_id=notification_id,

    )

    await db.commit()
    return success_response(data=None)






@router.post("/read_all")
async def set_all_notifications_read(
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database),
):
    """
    将当前用户的所有未读通知标记为已读。
    业务/实现提示：
    - 调用 crud.mark_all_read(db, user.id)
    - await db.commit()
    - 返回 success_response()
    """
    await notifications.mark_all_read(db,user_id=user.id)
    await db.commit()
    success_response(data=None)













