from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class InvoiceBase(BaseModel):
    customer_id: int
    amount: float
    status: str
    due_date: datetime

class InvoiceCreate(InvoiceBase):
    pass

class InvoiceResponse(InvoiceBase):
    id: int
    user_id: int
    issued_at: datetime

    class Config:
        from_attributes = True

class VendorAccessResponse(BaseModel):
    vendor_id: int
    access_mode: str
    source: str
    valid_until: Optional[datetime] = None

    class Config:
        from_attributes = True
