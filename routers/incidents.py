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
from crud import incidents,comments,events
from models.incident_events import IncidentEventType
from models.incidents import IncidentStatus
from models.users import User
from schemas.events import IncidentEventPublic
from schemas.incidents import (
    IncidentCreateRequest,
    IncidentPublic,
    IncidentStatusUpdateRequest, IncidentAssignRequest,
)
from schemas.comments import CommentCreateRequest,CommentPublic
from services.notifications import build_incident_assigned_message, create_notification_for_user, \
    build_comment_added_message, create_notifications_bulk, build_status_changed_message
from utils.auth import get_current_user, require_superuser
from utils.response import success_response
from services.incidents import can_view_incident,can_assign_incident,can_comment_incident,can_change_status,get_incident
from utils.cache import get_cache_json, set_cache, make_cache_key

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

    cache_key = make_cache_key(
        prefix="incidents:detail:v1",
        parts={
            "incident_id": incident_id,
            "user_id": user.id,
            "is_admin": user.is_superuser,
        },
    )
    cached = await get_cache_json(cache_key)
    if cached is not None:
        return success_response(data=cached)


    """详情可见性规则（Step 6）：reporter / assignee / admin 可看"""
    incident = await get_incident(db,incident_id=incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    if not await can_view_incident(db, user=user, incident=incident):
        raise HTTPException(403, "low rights")

    data = IncidentPublic.model_validate(incident).model_dump()
    await set_cache(cache_key,data)
    return success_response(data=data)


@router.post("/{incident_id}/assign")
async def assign_incident(
        incident_id: uuid.UUID,
        payload: IncidentAssignRequest,
        admin: User = Depends(require_superuser),
        db: AsyncSession = Depends(get_database),
):
    """
    管理员指派 incident 给某个用户：
    - 设置 assignee_id
    - 如果当前 status 为 OPEN，则自动改为 TRIAGED
    - 写入 timeline 事件：
      - ASSIGNED（如果 assignee 发生变化）
      - （可选）如果 OPEN -> TRIAGED，则再写一条 STATUS_CHANGED
    """
    incident = await get_incident(db,incident_id=incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    old_assignee_id = incident.assignee_id
    new_assignee_id = payload.assignee_id

    # 1) 更新 assignee
    incident.assignee_id = new_assignee_id

    # 2) 只有在发生变化时，才写 ASSIGNED 事件（避免 timeline 噪音）
    if old_assignee_id != new_assignee_id:
        await events.create_event(
            db,
            incident_id=incident.id,
            actor_id=admin.id,
            type_=IncidentEventType.ASSIGNED,
            payload={
                "from": str(old_assignee_id) if old_assignee_id else None,
                "to": str(new_assignee_id),
            },
            summary="Incident assigned",
        )

    # 3) OPEN 被指派后自动 TRIAGED（并可记录状态变更事件）
    if incident.status == IncidentStatus.OPEN:
        old_status = str(incident.status)
        incident.status = IncidentStatus.TRIAGED

        # 可选但推荐：让 timeline 能看出状态为何变化
        await events.create_event(
            db,
            incident_id=incident.id,
            actor_id=admin.id,
            type_=IncidentEventType.STATUS_CHANGED,
            payload={"from": old_status, "to": str(incident.status)},
            summary=f"Status changed: {old_status} -> {incident.status}",
        )
        message = build_incident_assigned_message(incident.title)
        await create_notification_for_user(
            db=db,
            user_id=new_assignee_id,
            event_type="INCIDENT_ASSIGNED",
            ref_type="incident",
            ref_id=incident.id,
            message=message,
        )

    await db.commit()
    await db.refresh(incident)

    data = IncidentPublic.model_validate(incident)
    return success_response(data=data)



@router.patch("/{incident_id}/status")
async def update_incident_status(
        incident_id: uuid.UUID,
        payload: IncidentStatusUpdateRequest,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database),
):
    incident = await get_incident(db,incident_id=incident_id)

    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    if not await can_change_status(db=db,user=user,incident=incident):
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

    old_status = str(incident.status)
    incident.status = IncidentStatus(target)

    event = await events.create_event(
        db,
        incident_id=incident.id,
        actor_id=user.id,
        type_=IncidentEventType.STATUS_CHANGED,
        payload={"from": old_status, "to": target},
        summary=f"Status changed: {old_status} -> {target}",
    )

    targets: set[uuid.UUID] = set()
    reporter_id = getattr(incident, "reporter_id", None)
    assignee_id = getattr(incident, "assignee_id", None)

    if reporter_id:
        targets.add(reporter_id)  # type: ignore[arg-type]
    if assignee_id:
        targets.add(assignee_id)  # type: ignore[arg-type]

    # 不通知评论者本人（避免自通知）
    targets.discard(user.id)

    if targets:
        message = build_comment_added_message(incident.title, commenter_email=user.email)
        await create_notifications_bulk(
            db=db,
            user_ids=list(targets),
            event_type="COMMENT_ADDED",
            ref_type="incident",
            ref_id=incident.id,
            message=message,
        )

    await db.commit()
    await db.refresh(incident)

    data = IncidentPublic.model_validate(incident)
    return success_response(data=data)


@router.post("/{incident_id}/comments")
async def create_incident_comment(
        incident_id: uuid.UUID,
        payload:CommentCreateRequest,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database),
):
    """
    需要完成的业务目标：
    1) 查询 incident 是否存在（不存在 -> 404）
       - 用 incidents.get_incident_by_id(db, incident_id)
    2) 权限判断：admin / reporter / assignee 才能评论
       - 复用你 get_incident_detail 的 is_able_to_view 逻辑即可
       - 无权限 -> 403
    3) 调用 CRUD：comment_crud.create_comment(db, incident_id=..., author_id=user.id, content=payload.content)
    4) router 层 commit + refresh comment
    5) 返回 success_response(data=CommentPublic.model_validate(comment))
    """
    incident = await incidents.get_incident_by_id(db,incident_id)
    if not incident:
        raise HTTPException(status_code=404,detail="Incident not found")

    is_able_to_comment = await can_comment_incident(db=db,user=user,incident=incident)

    if is_able_to_comment:
        comment = await comments.create_comment(
            db,
            incident_id=incident_id,
            author_id=user.id,
            content=payload.content
        )

        targets: set[uuid.UUID] = set()
        reporter_id = getattr(incident, "reporter_id", None)
        assignee_id = getattr(incident, "assignee_id", None)

        if reporter_id:
            targets.add(reporter_id)  # type: ignore[arg-type]
        if assignee_id:
            targets.add(assignee_id)  # type: ignore[arg-type]

        # 不通知评论者本人（避免自通知）
        targets.discard(user.id)

        if targets:
            message = build_comment_added_message(incident.title, commenter_email=user.email)
            await create_notifications_bulk(
                db=db,
                user_ids=list(targets),
                event_type="COMMENT_ADDED",
                ref_type="incident",
                ref_id=incident.id,
                message=message,
            )






        await db.commit()
        await db.refresh(comment)

        data = CommentPublic.model_validate(comment)
        return success_response(data=data)
    else:
        raise HTTPException(status_code=403, detail="low rights")


@router.get("/{incident_id}/comments")
async def list_incident_comments(
        incident_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database),
):
    """
    需要完成的业务目标：
    1) 查询 incident 是否存在（不存在 -> 404）
    2) 权限判断：admin / reporter / assignee 才能查看评论（同 detail）
    3) 参数保护：
       - limit: 最小 1；最大建议 100
       - offset: 最小 0
    4) 调用 CRUD：comment_crud.list_comments_by_incident(db, incident_id=..., limit=..., offset=..., order="desc")
    5) 返回 success_response(data=[CommentPublic.model_validate(c) for c in comments])
    """
    incident = await incidents.get_incident_by_id(db,incident_id)
    if not incident:
        raise HTTPException(status_code=404,detail="Incident not found")

    is_able_to_comment = await can_comment_incident(db=db,user=user,incident=incident)

    if is_able_to_comment:
        comment_list = await comments.list_comments_by_incident(
            db,
            incident_id=incident_id,
            limit=limit,
            offset=offset,
            order="desc"
        )
        data = [CommentPublic.model_validate(u) for u in comment_list]

        return success_response(data=data)

    else:
        raise HTTPException(status_code=403, detail="low rights")



@router.get("/{incident_id}/timeline")
async def get_incident_timeline(
        incident_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database),
):
    """
    需要完成的业务目标：
    1) incident 必须存在（不存在 -> 404）
    2) 权限：admin / reporter / assignee 可看（同 detail）
    3) 参数保护：limit 1~100, offset >=0
    4) 调用 CRUD：events.list_events_by_incident(...)
    5) 返回 success_response(data=[IncidentEventPublic.model_validate(e) ...])
    """
    incident = await incidents.get_incident_by_id(db,incident_id)

    if not incident:
        raise HTTPException(status_code=404,detail="Incident not found")

    is_able_to_view = await can_view_incident(db=db,user=user,incident=incident)

    if not is_able_to_view:
        raise HTTPException(status_code=403,detail="Low rights")

    event_list = await events.list_events_by_incident(
        db,
        incident_id=incident_id,
        limit=limit,
        offset=offset
    )

    data = [IncidentEventPublic.model_validate(u) for u in event_list]

    return success_response(data=data)



@router.get("/search")
async def list_incidents(
        q: str | None = None,
        status: str | None = None,
        team_id: uuid.UUID | None = None,
        assignee_id: uuid.UUID | None = None,
        reporter_id: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database),
):
    q_norm = _normalize_query(q)

    if limit < 1:
        limit = 1
    if limit > 100:
        limit = 100
    if offset < 0:
        offset = 0

    if status is not None:
        try:
            status_enum = IncidentStatus(status)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid status")


    cache_key = make_cache_key(
        prefix="incident:search:v1",
        parts={
            "user_id":user.id,
            "is_admin": user.is_superuser,
            "q": q_norm,
            "status": status,
            "team_id": team_id,
            "assignee_id": assignee_id,
            "reporter_id": reporter_id,
            "limit": limit,
            "offset": offset,
        },
    )
    cached = await get_cache_json(cache_key)
    if cached is not None:
        return success_response(data=cached)


    incident_list = await incidents.search_incidents(
        db,
        user_id=user.id,
        is_admin=user.is_superuser,
        q=q_norm,
        status=status,
        team_id=team_id,
        assignee_id=assignee_id,
        reporter_id=reporter_id,
        limit=limit,
        offset=offset,
    )

    data = [IncidentPublic.model_validate(x).model_dump() for x in incident_list]
    await set_cache(cache_key,data)
    return success_response(data=data)


def _normalize_query(q: str | None) -> str | None:
    """
    规范化搜索关键字：
    - 去掉首尾空格
    - 把连续空白（空格/制表/换行）压缩成单空格
    - 如果最终为空，返回 None
    """
    if q is None:
        return None
    normalized = " ".join(q.split())
    return normalized or None
