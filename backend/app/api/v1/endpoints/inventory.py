from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database.session import get_async_session
from app.core.database.models import Product, ProductUpdate
from app.core.rate_limit import limiter
from app.core.config import settings
from app.repositories.product import product_repo
from sqlmodel import Session
from app.core.database.session import engine
from app.api.deps import get_current_user
from app.core.database.models import User

router = APIRouter()

@router.get("/products/", response_model=List[Product])
@limiter.limit(settings.RATE_LIMIT_READ_PRODUCTS)
async def read_products(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    type: Optional[str] = None,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    return await product_repo.get_all_async(session, user_id=current_user.id, skip=skip, limit=limit, type=type)

@router.post("/products/", response_model=Product)
@limiter.limit(settings.RATE_LIMIT_WRITE_PRODUCTS)
async def create_product(
    request: Request, 
    product: Product, 
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    product.user_id = current_user.id
    return await product_repo.create_async(session, product)

@router.get("/products/{product_id}", response_model=Product)
@limiter.limit(settings.RATE_LIMIT_READ_PRODUCTS)
async def read_product(
    request: Request, 
    product_id: int, 
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    product = await product_repo.get_by_id_async(session, product_id, user_id=current_user.id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.patch("/products/{product_id}", response_model=Product)
@limiter.limit(settings.RATE_LIMIT_UPDATE_PRODUCTS)
async def update_product(
    request: Request, 
    product_id: int, 
    product_update: ProductUpdate, 
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    product = await product_repo.get_by_id_async(session, product_id, user_id=current_user.id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return await product_repo.update_async(session, product, product_update)

@router.delete("/products/{product_id}")
@limiter.limit(settings.RATE_LIMIT_DELETE_PRODUCTS)
async def delete_product(
    request: Request, 
    product_id: int, 
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    product = await product_repo.get_by_id_async(session, product_id, user_id=current_user.id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    await product_repo.delete_async(session, product)
    return {"ok": True}

# === STOCK MANAGEMENT ENDPOINTS ===

@router.post("/products/{product_id}/stock/adjust")
@limiter.limit(settings.RATE_LIMIT_WRITE_PRODUCTS)
async def adjust_stock(
    request: Request, 
    product_id: int, 
    quantity_change: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Ajusta el stock de un producto (cantidad positiva para agregar, negativa para restar)"""
    with Session(engine) as sync_session:
        updated_product = product_repo.update_stock(sync_session, product_id, current_user.id, quantity_change)
        
    if not updated_product:
        raise HTTPException(status_code=404, detail="Product not found or invalid stock adjustment")
    
    return updated_product

@router.get("/products/stock/low")
@limiter.limit(settings.RATE_LIMIT_READ_PRODUCTS)
async def get_low_stock_products(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Obtiene productos con stock bajo (por debajo del umbral configurado)"""
    with Session(engine) as sync_session:
        return product_repo.check_low_stock(sync_session, current_user.id)

class BulkStatusUpdateRequest(BaseModel):
    product_ids: List[int]
    new_status: str

@router.post("/products/bulk/status")
@limiter.limit(settings.RATE_LIMIT_WRITE_PRODUCTS)
async def bulk_update_product_status(
    request: Request,
    body: BulkStatusUpdateRequest,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    valid_statuses = ["active", "paused", "archived"]
    if body.new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    with Session(engine) as sync_session:
        updated_count = product_repo.bulk_update_stock_status(sync_session, current_user.id, body.product_ids, body.new_status)
    return {"updated_count": updated_count, "status": body.new_status}
