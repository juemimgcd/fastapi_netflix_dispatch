from fastapi import APIRouter, Depends, HTTPException
from schemas.auth import RegisterRequest, LoginRequest, UserAuthResponse
from sqlalchemy.ext.asyncio import AsyncSession
from conf.db_conf import get_database
from utils.security import hash_password
from utils.security import create_access_token
from schemas.users import UserPublic
from crud import users
from models.users import User
from utils.response import success_response
from utils.auth import get_current_user

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


@router.get("/info")
async def get_user_info(user: User = Depends(get_current_user)):
    data = UserPublic.model_validate(user)
    return success_response(data=data)
