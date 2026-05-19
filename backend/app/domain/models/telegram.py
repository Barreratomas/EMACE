from datetime import datetime, timezone
from typing import Optional, List
from sqlmodel import Field, SQLModel, Column, JSON
from app.infrastructure.security import sanitize_html

# Integración de Telegram por Vendor (Bring Your Own Bot)
class VendorTelegramIntegration(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    vendor_id: int = Field(foreign_key="user.id", unique=True)
    bot_username: str = Field(index=True)
    bot_token_encrypted: str
    webhook_secret: str = Field(index=True)
    is_active: bool = Field(default=True)
    last_error: Optional[str] = None
    state: str = Field(default="active")
    paused_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    paused_by_user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

class VendorMtprotoSession(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    vendor_id: int = Field(foreign_key="user.id", unique=True)
    session_encrypted: Optional[str] = None
    phone_number: Optional[str] = None
    device_info: Optional[str] = None
    enabled: bool = Field(default=False)
    status: str = Field(default="inactive")
    allowed_chats: List[str] = Field(default=[], sa_column=Column(JSON))
    last_error: Optional[str] = None
    last_heartbeat_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
