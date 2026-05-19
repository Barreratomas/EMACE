from datetime import datetime, timezone
from typing import Optional, List
from sqlmodel import Field, SQLModel, Column, JSON, Relationship
from pydantic import field_validator
from app.infrastructure.security import sanitize_html

# Modelo de Rol (RBAC Dinámico)
class Role(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: Optional[str] = None
    # Permisos como lista de strings (ej: ["products:read", "products:write"])
    permissions: List[str] = Field(default=[], sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    # Relación inversa
    users: List["User"] = Relationship(back_populates="role")

    @field_validator("name", "description")
    @classmethod
    def sanitize_strings(cls, v):
        if isinstance(v, str):
            return sanitize_html(v)
        return v

class UserIAMPolicyLink(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    policy_id: int = Field(foreign_key="iampolicy.id", primary_key=True)

# Modelo de Usuario (Dueño de Tienda / Vendedor) - SaaS User
class User(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str = Field(unique=True, index=True)
    password_hash: Optional[str] = None
    role_id: Optional[int] = Field(default=None, foreign_key="role.id")
    is_active: bool = Field(default=True)
    last_login: Optional[datetime] = None
    failed_attempts: int = Field(default=0)
    parent_id: Optional[int] = Field(default=None, foreign_key="user.id")
    
    # MFA (Preparación Fase 9.2)
    mfa_enabled: bool = Field(default=False)
    totp_secret: Optional[str] = None
    
    plan_type: str = Field(default="basic") # basic, premium, enterprise
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    # Relaciones
    role: Optional[Role] = Relationship(back_populates="users")
    parent: Optional["User"] = Relationship(back_populates="children", sa_relationship_kwargs={"remote_side": "User.id"})
    children: List["User"] = Relationship(back_populates="parent")
    policies: List["IAMPolicy"] = Relationship(back_populates="users", link_model=UserIAMPolicyLink)

    @field_validator("name")
    @classmethod
    def sanitize_strings(cls, v):
        if isinstance(v, str):
            return sanitize_html(v)
        return v

class IAMPolicy(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)
    description: Optional[str] = None
    permissions: List[str] = Field(default=[], sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    users: List["User"] = Relationship(back_populates="policies", link_model=UserIAMPolicyLink)

    @field_validator("name", "description")
    @classmethod
    def sanitize_strings(cls, v):
        if isinstance(v, str):
            return sanitize_html(v)
        return v

# Modelo de Refresh Token (Gestión de Sesiones)
class RefreshToken(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    token: str = Field(unique=True, index=True)
    user_id: int = Field(foreign_key="user.id")
    expires_at: datetime
    is_revoked: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
