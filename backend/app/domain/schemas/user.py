from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict

class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None

class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role_id: Optional[int]
    is_active: bool
    plan_type: str
    last_login: Optional[datetime] = None

class PasswordChange(BaseModel):
    old_password: str
    new_password: str
