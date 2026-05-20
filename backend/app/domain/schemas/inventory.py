from typing import Optional
from pydantic import BaseModel, field_validator, ConfigDict
from app.infrastructure.security import sanitize_html

class ProductBase(BaseModel):
    name: str
    category: str
    price: float
    type: str = "physical"
    status: str = "active"
    stock: Optional[int] = None
    min_stock_threshold: Optional[int] = 5
    sla: Optional[str] = None
    description: str

    @field_validator("name", "category", "sla", "description")
    @classmethod
    def sanitize_strings(cls, v):
        if isinstance(v, str):
            return sanitize_html(v)
        return v

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
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

class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
