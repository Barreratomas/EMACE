from datetime import datetime, timezone
from typing import Optional, List
from sqlmodel import Field, SQLModel, Column, JSON, Relationship
from pydantic import field_validator
from app.core.security import sanitize_html

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

# Estado de Acceso del Vendor (Billing)
class VendorAccessState(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    vendor_id: int = Field(foreign_key="user.id", unique=True)
    access_mode: str  # subscription | lifetime
    source: str  # trial | paid_subscription | lifetime_purchase
    valid_until: Optional[datetime] = None  # NULL para lifetime
    subscription_id_mp: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

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

# Eventos de Billing (Webhooks e Idempotencia)
class BillingEvent(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    vendor_id: int = Field(foreign_key="user.id")
    event_type: str
    mp_event_id: Optional[str] = Field(default=None, index=True)  # para idempotencia si aplica
    raw_payload: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    normalized: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

# Auditoría de cambios en VendorAccessState
class VendorAccessAudit(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    vendor_id: int = Field(foreign_key="user.id")
    actor_user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    action: str  # set_trial, extend_subscription, set_past_due, set_lifetime, cancel_subscription
    old_state: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    new_state: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

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

# Modelo de Factura
class Invoice(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customer.id") # Cliente final
    user_id: int = Field(foreign_key="user.id") # Vendedor (Tenant Context)
    amount: float
    status: str # paid, pending, overdue, disputed
    due_date: datetime
    issued_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

# Modelo de Ticket (Soporte)
class Ticket(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customer.id")
    user_id: int = Field(foreign_key="user.id") # Vendedor (Tenant Context)
    subject: str
    description: str
    priority: str # low, medium, high, critical
    status: str # open, in_progress, resolved, closed
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

# Modelo de Pedido (Order) - Preparación Fase 10.3
class Order(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customer.id")
    user_id: int = Field(foreign_key="user.id")
    total_amount: float = Field(default=0.0)
    status: str = Field(default="pending") # pending, confirmed, shipped, delivered, cancelled
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

# Modelo de Item de Pedido
class OrderItem(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="order.id")
    product_id: int = Field(foreign_key="product.id")
    quantity: int
    unit_price: float

# Modelo de Carrito de Compras (Cart)
class Cart(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customer.id", unique=True)
    user_id: int = Field(foreign_key="user.id")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

# Modelo de Item de Carrito
class CartItem(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    cart_id: int = Field(foreign_key="cart.id")
    product_id: int = Field(foreign_key="product.id")
    quantity: int = Field(default=1)

# Logs de Auditoría (Para QA y Trazabilidad)
class AuditLog(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id") # Vendedor responsable
    agent_name: str
    action: str
    details: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

class Product(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id") # Inventario del Vendedor
    name: str
    category: str
    price: float
    type: str = Field(default="physical") # physical, service
    status: str = Field(default="active") # active, paused, archived
    stock: Optional[int] = Field(default=None) # Solo para físicos
    min_stock_threshold: Optional[int] = Field(default=5) # Alerta de stock bajo
    sla: Optional[str] = Field(default=None) # Solo para servicios (ej: "24h response")
    description: str

    @field_validator("name", "category", "sla", "description")
    @classmethod
    def sanitize_strings(cls, v):
        if isinstance(v, str):
            return sanitize_html(v)
        return v

class ProductUpdate(SQLModel):
    name: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    type: Optional[str] = None
    status: Optional[str] = None
    stock: Optional[int] = None
    min_stock_threshold: Optional[int] = None
    sla: Optional[str] = None
    description: Optional[str] = None

    @field_validator("name", "category", "sla", "description")
    @classmethod
    def sanitize_strings(cls, v):
        if isinstance(v, str):
            return sanitize_html(v)
        return v

# Modelo de Cita/Reunión (Nuevo para Fase de Escalamiento)
class Appointment(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customer.id")
    user_id: int = Field(foreign_key="user.id") # Vendedor
    agent_role: str # sales, tech
    datetime_slot: datetime
    status: str = "scheduled" # scheduled, cancelled, completed
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

# Historial de Chat (Auditoría y Trazabilidad Legal)
class ChatHistory(SQLModel, table=True):
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id") # Vendedor
    session_id: str = Field(index=True) # ID de la sesión/hilo de LangGraph
    user_message: str
    agent_message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    metadata_json: Optional[str] = None # JSON stringificado con detalles extra
