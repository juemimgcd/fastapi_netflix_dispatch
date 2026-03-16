"""
Incident Comment 相关 CRUD（只做数据库层的读写）

原则：
- CRUD 层只关心“怎么查/怎么写”
- 不在这里做 HTTPException（那是 router/service 层的职责）
- 不 commit（保持你项目风格：router 层 commit）
"""
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.incident_comments import IncidentComment


async def create_comment(
        db: AsyncSession,
        *,
        incident_id: uuid.UUID,
        author_id: uuid.UUID,
        content: str,
) -> IncidentComment:
    """
    需要完成的业务/数据目标：
    - 新建 IncidentComment(incident_id, author_id, content)
    - db.add(comment)
    - 返回 comment（不 commit，不 refresh）

    注意：
    - incident 是否存在：router 层负责
    - 权限判断：router 层负责
    """
    comment = IncidentComment(
        incident_id=incident_id,
        author_id=author_id,
        content=content)

    db.add(comment)
    return comment


async def list_comments_by_incident(
        db: AsyncSession,
        *,
        incident_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
        order: str = "desc",
) -> list[IncidentComment]:
    """
    需要完成的业务/数据目标：
    - 查询某个 incident 下的评论列表
    - 支持分页 limit/offset
    - 按 created_at 排序（desc: 最新在前；asc: 最早在前）
    - 返回 list[IncidentComment]

    注意：
    - limit 上限保护可在 router 或这里实现（建议 router 先 clamp）
    """

    stmt = (
        select(IncidentComment)
        .where(IncidentComment.incident_id == incident_id)
        .order_by(IncidentComment.created_at.desc())
        .offset(offset)
        .limit(limit)

    )

    result = await db.execute(stmt)

    comment_list = list(result.scalars().all())
    return comment_list


async def get_comment_by_id(
        db: AsyncSession,
        *,
        comment_id: uuid.UUID,
) -> IncidentComment | None:
    """
    需要完成的业务/数据目标：
    - 通过 comment_id 获取单条评论
    - 返回 comment 或 None

    用途：
    - 未来做编辑/删除 comment
    """

    stmt = (
        select(IncidentComment)
        .where(IncidentComment.id == comment_id)

    )
    result = await db.execute(stmt)

    comment = result.scalar_one_or_none()

    return comment





