from typing import Optional
from sqlmodel import Field, SQLModel
from pydantic import field_validator
from app.infrastructure.security import sanitize_html

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
