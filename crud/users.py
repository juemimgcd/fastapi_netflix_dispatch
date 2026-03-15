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


async def get_user_by_email(db: AsyncSession, email: EmailStr):
    sql = select(User).where(User.email == email)
    result = await db.execute(sql)

    user = result.scalar_one_or_none()
    return user




async def authenticate_user(db:AsyncSession,email:EmailStr,password:str):
    user = await get_user_by_email(db,email)
    if not user:
        return None
    if not security.verify_password(password,user.password_hash):
        return None
    return user



async def create_access_token(*, subject: str, expires_minutes: int | None = None, extra_claims: dict[str, Any] | None = None) -> str:

    now = datetime.now()
    expire = datetime.now() + timedelta(days=7)

    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)