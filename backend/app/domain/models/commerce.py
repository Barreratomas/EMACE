from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel

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
