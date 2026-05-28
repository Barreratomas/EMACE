from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.session import get_async_session
from app.domain.models import User
from app.domain.schemas.inventory import ProductCreate, ProductUpdate, ProductResponse
from app.infrastructure.adapters.rate_limit import limiter
from app.infrastructure.config import settings
from app.infrastructure.repositories.product import product_repo
from app.infrastructure.repositories.audit import audit_repo
from app.infrastructure.database.session import engine
from app.interfaces.api.deps import get_current_user, get_tenant_owner_id
from app.application.use_cases.inventory_use_cases import InventoryUseCases

router = APIRouter()
inventory_use_cases = InventoryUseCases(product_repo, audit_repo)

@router.get("/products/", response_model=List[ProductResponse])
@limiter.limit(settings.RATE_LIMIT_READ_PRODUCTS)
async def read_products(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    type: Optional[str] = None,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Lista los productos del catálogo con soporte para paginación y filtrado"""
    tenant_id = get_tenant_owner_id(current_user)
    return await inventory_use_cases.list_products(
        session, user_id=tenant_id, skip=skip, limit=limit, type=type
    )

@router.post("/products/", response_model=ProductResponse)
@limiter.limit(settings.RATE_LIMIT_WRITE_PRODUCTS)
async def create_product(
    request: Request, 
    product_in: ProductCreate, 
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Crea un nuevo producto en el inventario del vendor"""
    tenant_id = get_tenant_owner_id(current_user)
    return await inventory_use_cases.create_product(session, tenant_id, product_in)

@router.get("/products/{product_id}", response_model=ProductResponse)
@limiter.limit(settings.RATE_LIMIT_READ_PRODUCTS)
async def read_product(
    request: Request, 
    product_id: int, 
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Obtiene el detalle completo de un producto específico"""
    tenant_id = get_tenant_owner_id(current_user)
    product = await inventory_use_cases.get_product(session, product_id, tenant_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.patch("/products/{product_id}", response_model=ProductResponse)
@limiter.limit(settings.RATE_LIMIT_UPDATE_PRODUCTS)
async def update_product(
    request: Request, 
    product_id: int, 
    product_update: ProductUpdate, 
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Actualiza parcialmente los datos de un producto existente"""
    tenant_id = get_tenant_owner_id(current_user)
    product = await inventory_use_cases.update_product(session, product_id, tenant_id, product_update)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.delete("/products/{product_id}")
@limiter.limit(settings.RATE_LIMIT_DELETE_PRODUCTS)
async def delete_product(
    request: Request, 
    product_id: int, 
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Elimina permanentemente un producto del catálogo"""
    tenant_id = get_tenant_owner_id(current_user)
    success = await inventory_use_cases.delete_product(session, product_id, tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
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
    tenant_id = get_tenant_owner_id(current_user)
    updated_product = await inventory_use_cases.adjust_stock(session, product_id, tenant_id, quantity_change)
    if not updated_product:
        raise HTTPException(status_code=404, detail="Product not found or invalid stock adjustment")
    return updated_product

@router.post("/import")
@limiter.limit(settings.RATE_LIMIT_WRITE_PRODUCTS)
async def import_products(
    request: Request,
    file: UploadFile = File(...),
    conflict_strategy: str = "skip", # skip, update
    dry_run: bool = False,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Importa productos de forma masiva desde un archivo CSV o Excel.
    Soporta previsualización (dry_run) y estrategias de conflicto.
    """
    filename = file.filename.lower()
    if not (filename.endswith('.csv') or filename.endswith('.xlsx')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de archivo no soportado. Use .csv o .xlsx"
        )

    try:
        contents = await file.read()
        tenant_id = get_tenant_owner_id(current_user)
        return await inventory_use_cases.import_products(
            session, tenant_id, contents, filename, conflict_strategy, dry_run
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar el archivo: {str(e)}"
        )
    finally:
        await file.close()


@router.get("/import/template")
@limiter.limit(settings.RATE_LIMIT_READ_PRODUCTS)
async def download_import_template(
    request: Request,
    format: str = Query("csv", pattern="^(csv|xlsx)$"),
    current_user: User = Depends(get_current_user),
):
    """
    Devuelve una plantilla de ejemplo para la carga masiva de productos.
    Soporta formatos CSV y Excel (.xlsx).
    """
    template = inventory_use_cases.get_import_template(format)
    return StreamingResponse(
        template["content"],
        media_type=template["media_type"],
        headers={"Content-Disposition": f'attachment; filename="{template["filename"]}"'},
    )

@router.get("/products/stock/low")
@limiter.limit(settings.RATE_LIMIT_READ_PRODUCTS)
async def get_low_stock_products(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Obtiene productos con stock bajo (por debajo del umbral configurado)"""
    return await inventory_use_cases.get_low_stock_products(session, current_user.id)

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
    """Actualiza masivamente el estado de múltiples productos"""
    valid_statuses = ["active", "paused", "archived"]
    if body.new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    updated_count = await inventory_use_cases.bulk_update_status(
        session, current_user.id, body.product_ids, body.new_status
    )
    return {"updated_count": updated_count, "status": body.new_status}
