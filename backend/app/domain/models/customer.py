from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel
from pydantic import field_validator
from app.infrastructure.security import sanitize_html

# Modelo de Cliente Final (Customer) - B2B2C
class Customer(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id") # El vendedor al que pertenece este cliente
    name: str
    email: str = Field(index=True) # Puede repetirse entre vendors
    phone: Optional[str] = None
    telegram_chat_id: Optional[str] = Field(default=None, index=True) # ID de Telegram para comunicación
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    @field_validator("name", "phone")
    @classmethod
    def sanitize_strings(cls, v):
        if isinstance(v, str):
            return sanitize_html(v)
        return v
