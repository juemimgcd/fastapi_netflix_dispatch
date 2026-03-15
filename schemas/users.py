import uuid
from pydantic import BaseModel, EmailStr, ConfigDict


class UserPublic(BaseModel):
    id: uuid.UUID
    email: EmailStr
    is_active: bool

    model_config = ConfigDict(from_attributes=True)



