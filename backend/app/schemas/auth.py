from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from typing import List

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    role: Optional[str] = None
    permissions: List[str] = []
    type: str = "access"

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    # Usado opcionalmente para flujos particionados
    vendor_identifier: Optional[EmailStr] = None

class IAMLogin(BaseModel):
    email: EmailStr
    password: str
    vendor_identifier: EmailStr

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=12)
    name: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    name: str
    role_id: Optional[int]
    is_active: bool
    plan_type: str
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=12)

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None

class IAMUserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=12)
    name: str

class IAMUserResponse(BaseModel):
    id: int
    email: EmailStr
    name: str
    parent_id: int

    class Config:
        from_attributes = True

class IAMPolicyAssignRequest(BaseModel):
    policies: List[str]
    operation: str = Field(default="set")  # set | add | remove
