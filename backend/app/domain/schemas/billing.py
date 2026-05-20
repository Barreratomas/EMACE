from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class InvoiceBase(BaseModel):
    customer_id: int
    amount: float
    status: str
    due_date: datetime

class InvoiceCreate(InvoiceBase):
    pass

class InvoiceResponse(InvoiceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    issued_at: datetime

class VendorAccessResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    vendor_id: int
    access_mode: str
    source: str
    valid_until: Optional[datetime] = None
