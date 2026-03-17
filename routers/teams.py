import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from conf.db_conf import get_database
from crud import teams,users
from crud import team_memberships
from models.team_memberships import TeamRole
from models.users import User
from schemas.teams import (
    TeamCreateRequest,
    TeamMembershipAddRequest,
    TeamMembershipPublic,
    TeamPublic,
)
from utils.auth import get_current_user, require_superuser
from utils.response import success_response

router = APIRouter(prefix="/teams", tags=["teams"])


@router.post("")
async def create_team(
        payload: TeamCreateRequest,
        admin: User = Depends(require_superuser),
        db: AsyncSession = Depends(get_database),
):
    """
    业务目标：
    1) name 唯一：已存在 -> 400
    2) 创建 team
    3) 自动把 admin 加入为 OWNER（写 membership）
    4) commit + refresh
    """
    team = await teams.get_team_by_name(db,name=payload.name)
    if team:
        raise HTTPException(status_code=400,detail="Team already exits")

    team = await teams.create_team(db,name=payload.name)
    membership = team_memberships.add_membership(db,team_id=team.id,user_id=admin.id,role=TeamRole('OWNER'))

    await db.commit()
    await db.refresh(team)
    data = TeamPublic.model_validate(team)

    return success_response(data=data)




@router.get("")
async def list_teams(
        limit: int = 50,
        offset: int = 0,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database),
):
    """
    业务目标：
    - MVP：任何登录用户可列出 teams（或只列出自己所在 teams，你二选一）
    """


    team_list = await teams.list_teams(db,limit=limit,offset=offset)

    data = [TeamPublic.model_validate(u) for u in team_list]

    return success_response(data=data)




@router.post("/{team_id}/members")
async def add_team_member(
        team_id: uuid.UUID,
        payload: TeamMembershipAddRequest,
        admin: User = Depends(require_superuser),
        db: AsyncSession = Depends(get_database),
):
    """
    业务目标（MVP 简化版）：
    - 只有 admin 能拉人进 team（你也可以升级为：team OWNER 也能拉人）
    - team 必须存在
    - user 必须存在
    - 重复 membership -> 400
    - commit + refresh
    """
    team = await teams.get_team_by_id(db,team_id=team_id)
    if not team:
        raise HTTPException(status_code=404,detail="Team not found")

    user = await users.get_user_by_id(db,user_id=admin.id)
    if not user:
        raise HTTPException(status_code=404,detail="User not found")

    member_ship = await team_memberships.get_membership(
        db,
        team_id=team_id,
        user_id=payload.user_id
    )
    if member_ship:
        raise HTTPException(status_code=400, detail="User already in team")
    role = TeamRole(payload.role)
    membership = await team_memberships.add_membership(
        db,
        team_id=team_id,
        user_id=payload.user_id,
        role=role,
    )
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        # 双写保护：并发下仍可能触发唯一约束
        raise HTTPException(status_code=400, detail="User already in team")

    await db.refresh(membership)
    data = TeamMembershipPublic.model_validate(membership)
    return success_response(data=data)



@router.get("/{team_id}/members")
async def list_team_members(
        team_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database),
):
    """
    业务目标：
    - team 必须存在
    - 权限：admin 或 team member 可看成员列表（你选择）
    """
    team = await teams.get_team_by_id(db,team_id=team_id)
    if not team:
        raise HTTPException(status_code=404,detail="Team not found")


    if not user.is_superuser:
        membership = await team_memberships.get_membership(db, team_id=team_id, user_id=user.id)
        if not membership:
            raise HTTPException(status_code=403, detail="low rights")


    membership_list = await team_memberships.list_team_memberships(
        db,
        team_id=team_id,
        limit=limit,
        offset=offset,
    )
    data = [TeamMembershipPublic.model_validate(m) for m in membership_list]
    return success_response(data=data)

























