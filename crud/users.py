import uuid
from datetime import datetime, timezone, timedelta
from typing import Any
from jose import jwt
from conf.settings import settings
from models.users import User
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from utils import security
from fastapi import HTTPException, status
from pydantic import EmailStr
from models.incidents import Incident



async def get_user_by_email(db: AsyncSession, email: EmailStr):
    sql = select(User).where(User.email == email)
    result = await db.execute(sql)

    user = result.scalar_one_or_none()
    return user


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()




async def authenticate_user(db:AsyncSession,email:EmailStr,password:str):
    user = await get_user_by_email(db,email)
    if not user:
        return None
    if not security.verify_password(password,user.password_hash):
        return None
    return user


async def get_all_users(db:AsyncSession):
    sql = select(User).order_by(User.created_at.desc())

    result = await db.execute(sql)
    return result.scalars().all()





