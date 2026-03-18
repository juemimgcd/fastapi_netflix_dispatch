"""
通知服务层（service）：封装高层通知创建/广播逻辑。
- service 层不做 commit（遵循项目风格：router 负责 commit/refresh）
- service 调用 crud.create_notification 等函数（你会实现 crud）
- 提供若干便捷函数，便于在业务点（assign, status change, comment）调用
"""

from __future__ import annotations
import uuid
from typing import Iterable, List
from sqlalchemy.ext.asyncio import AsyncSession

from crud import notifications as crud_notifications


async def create_notification_for_user(
        db: AsyncSession,
        user_id: uuid.UUID,
        event_type: str,
        ref_type: str,
        ref_id: uuid.UUID,
        message: str,
):
    """
    为单个用户创建一条通知（不 commit）。
    - 返回 crud.create_notification 的结果（Notification 实例）
    """
    return await crud_notifications.create_notification(
        db=db,
        user_id=user_id,
        event_type=event_type,
        ref_type=ref_type,
        ref_id=ref_id,
        message=message,
    )


async def create_notifications_bulk(
        db: AsyncSession,
        user_ids: Iterable[uuid.UUID],
        event_type: str,
        ref_type: str,
        ref_id: uuid.UUID,
        message: str,
) -> List:
    """
    为多个用户批量创建通知（不 commit）。
    - 用于一个事件需要通知多人（如指派给某人 + 报告人 + team）。
    - 返回创建的 Notification 实例列表（取决于 crud 实现是否返回）
    """
    res = []
    for uid in user_ids:
        n = await create_notification_for_user(
            db=db,
            user_id=uid,
            event_type=event_type,
            ref_type=ref_type,
            ref_id=ref_id,
            message=message,
        )
        res.append(n)
    return res


def build_incident_assigned_message(incident_title: str) -> str:
    return f"You are assigned to incident: {incident_title}"


def build_comment_added_message(incident_title: str, commenter_email: str) -> str:
    return f"New comment on \"{incident_title}\" by {commenter_email}"


def build_status_changed_message(incident_title: str, from_status: str, to_status: str) -> str:
    return f"Incident \"{incident_title}\" status changed: {from_status} -> {to_status}"