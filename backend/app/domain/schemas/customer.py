from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator, ConfigDict
from app.infrastructure.security import sanitize_html

class CustomerBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    telegram_chat_id: Optional[str] = None

    @field_validator("name", "phone")
    @classmethod
    def sanitize_strings(cls, v):
        if isinstance(v, str):
            return sanitize_html(v)
        return v

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    telegram_chat_id: Optional[str] = None

class CustomerResponse(CustomerBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime
