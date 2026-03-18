"""
通知相关的 CRUD 层 - 你实现函数体即可（下面仅保留函数签名与注释，按照项目约定 CRUD 层只做 DB 操作，不抛 HTTPException）。
路由层负责 commit/refresh/HTTPException。
"""

import uuid
from typing import List

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.notifications import Notification


async def create_notification(
        db: AsyncSession,
        user_id: uuid.UUID,
        event_type: str,
        ref_type: str,
        ref_id: uuid.UUID,
        message: str,
) -> Notification:
    """
    在 notifications 表里创建一条通知记录并返回该 Notification 对象。

    约定：
    - 不在这里 commit；由调用方（router）决定何时 commit
    - 返回新增的 Notification ORM 实例（未 refresh 也可以）
    """
    note = Notification(
        user_id=user_id,
        event_type=event_type,
        ref_type=ref_type,
        ref_id=ref_id,
        message=message
    )

    db.add(note)
    return note


async def get_notification_by_id(
        db: AsyncSession,
        notification_id:uuid.UUID
):
    stmt = (
        select(Notification)
        .where(Notification.id == notification_id)
    )
    res = await db.execute(stmt)

    return res.scalar_one_or_none()



async def list_notifications(
        db: AsyncSession,
        user_id: uuid.UUID,
        unread: bool | None = None,
        limit: int = 50,
        offset: int = 0,
) -> List[Notification]:
    """
    查询指定用户的通知列表（按 created_at 降序）。
    - unread: None 表示不过滤，True/False 表示只查未读/已读
    - limit/offset 分页
    返回 Notification 实例列表（不要把 ORM 转 dict，这里保持 ORM 对象）
    """
    stmt = (
        select(Notification)
        .where(Notification.user_id == user_id, unread=unread)
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    res = await db.execute(stmt)

    notes = res.scalars().all()

    return list(notes)


async def mark_notification_read(db: AsyncSession, notification_id: uuid.UUID) -> None:
    """
    将某条 notification 的 unread 字段设为 False。
    - 不在这里 commit，由调用方决定
    - 返回 None（或受你实现风格影响可返回更新行数）
    """
    stmt = (
        update(Notification)
        .where(Notification.id == notification_id)
        .values(unread=False)
    )
    await db.execute(stmt)


async def mark_all_read(db: AsyncSession, user_id: uuid.UUID) -> None:
    """
    将指定用户的所有未读通知标记为已读（unread=False）。
    - 不在这里 commit
    """

    stmt = (
        update(Notification)
        .where(Notification.user_id == user_id)
        .values(unread=False)
    )
    await db.execute(stmt)
