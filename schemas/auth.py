from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserAuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
