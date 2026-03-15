import uuid
from jose import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from conf.db_conf import get_database
from conf.settings import settings
from models.users import User
from typing import Optional

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
        creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
        db: AsyncSession = Depends(get_database)
) -> User:
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="not authenticated")
    token = creds.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        user_id = uuid.UUID(sub)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    resp = await db.execute(select(User).where(User.id == user_id))
    user = resp.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="User not found")

    return user
