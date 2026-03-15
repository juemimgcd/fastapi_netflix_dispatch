import uuid
from schemas.incidents import IncidentAssignRequest,IncidentPublic
from fastapi import APIRouter, Depends, HTTPException
from schemas.auth import RegisterRequest, LoginRequest, UserAuthResponse
from sqlalchemy.ext.asyncio import AsyncSession
from conf.db_conf import get_database
from utils.security import hash_password
from utils.security import create_access_token
from schemas.users import UserPublic, UserAdminPublic
from crud import users,incidents
from models.users import User
from models.incidents import IncidentStatus,Incident
from utils.response import success_response
from utils.auth import get_current_user, require_superuser

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register")
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_database)):
    user = await users.get_user_by_email(db, payload.email)
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(email=payload.email, password_hash=hash_password(payload.password))

    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = await create_access_token(subject=str(user.id))
    data = UserAuthResponse(access_token=token)
    return success_response(data=data)


@router.post("/login")
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_database)):
    user = await users.authenticate_user(db, payload.email, payload.password)

    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    token = await create_access_token(subject=str(user.id))
    data = UserAuthResponse(access_token=token)
    return success_response(data=data)


@router.get("/me")
async def get_user_info(user: User = Depends(get_current_user)):
    data = UserPublic.model_validate(user)
    return success_response(data=data)


@router.get("")
async def admin_list_users(
        admin: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_database)

):
    """
    管理员列出所有用户（为下一步“指派 incident 给某个用户”做准备）
    注意：
    - 只有 is_superuser=True 的用户才能访问（require_superuser）
    - 这里只返回必要字段，避免泄露敏感信息（如 password_hash）
    """

    user_list = await users.get_all_users(db)
    data = [UserAdminPublic.model_validate(u) for u in user_list]
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
    """
    incident = await incidents.get_incident_by_id(db, incident_id=incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident.assignee_id = payload.assignee_id

    if incident.status == IncidentStatus.OPEN:
        incident.status = IncidentStatus.TRIAGED

    await db.commit()
    await db.refresh(incident)

    data = IncidentPublic.model_validate(incident)
    return success_response(data=data)





























