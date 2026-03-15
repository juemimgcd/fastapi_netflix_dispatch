import uuid
from pydantic import BaseModel, EmailStr, ConfigDict


class UserPublic(BaseModel):
    id: uuid.UUID
    email: EmailStr
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class UserAdminPublic(BaseModel):
    """
    管理员视角的用户信息（用于指派/后台管理）
    """
    id: uuid.UUID
    email: EmailStr
    is_active: bool
    is_superuser: bool

    model_config = ConfigDict(from_attributes=True)
