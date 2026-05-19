from typing import Optional
from pydantic import BaseModel, EmailStr, Field

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

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=12)
