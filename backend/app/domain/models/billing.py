from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel, Column, JSON
from app.infrastructure.security import sanitize_html

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
