from typing import List, Optional
import io
import csv
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database.session import get_async_session
from app.core.database.models import Product, ProductUpdate
from app.core.rate_limit import limiter
from app.core.config import settings
from app.repositories.product import product_repo
from sqlmodel import Session
from app.core.database.session import engine
from app.api.deps import get_current_user, get_tenant_owner_id
from app.core.database.models import User
from sqlalchemy import select

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
    tenant_id = get_tenant_owner_id(current_user)
    return await product_repo.get_all_async(session, user_id=tenant_id, skip=skip, limit=limit, type=type)

@router.post("/products/", response_model=Product)
@limiter.limit(settings.RATE_LIMIT_WRITE_PRODUCTS)
async def create_product(
    request: Request, 
    product: Product, 
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    product.user_id = get_tenant_owner_id(current_user)
    return await product_repo.create_async(session, product)

@router.get("/products/{product_id}", response_model=Product)
@limiter.limit(settings.RATE_LIMIT_READ_PRODUCTS)
async def read_product(
    request: Request, 
    product_id: int, 
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    tenant_id = get_tenant_owner_id(current_user)
    product = await product_repo.get_by_id_async(session, product_id, user_id=tenant_id)
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
    tenant_id = get_tenant_owner_id(current_user)
    product = await product_repo.get_by_id_async(session, product_id, user_id=tenant_id)
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
    tenant_id = get_tenant_owner_id(current_user)
    product = await product_repo.get_by_id_async(session, product_id, user_id=tenant_id)
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
    tenant_id = get_tenant_owner_id(current_user)
    with Session(engine) as sync_session:
        updated_product = product_repo.update_stock(sync_session, product_id, tenant_id, quantity_change)
        
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
        if filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))

        df.columns = [c.strip().lower() for c in df.columns]

        required_cols = {'name', 'category', 'price'}
        missing_cols = required_cols - set(df.columns)
        if missing_cols:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Faltan columnas requeridas: {', '.join(missing_cols)}"
            )

        preview_data = []
        imported_count = 0
        updated_count = 0
        skipped_count = 0
        errors = []

        tenant_id = get_tenant_owner_id(current_user)
        existing_products_query = select(Product).where(Product.user_id == tenant_id)
        existing_result = await session.execute(existing_products_query)
        existing_map = {p.name.lower(): p for p in existing_result.scalars().all()}

        for index, row in df.iterrows():
            try:
                name = str(row['name']).strip()
                category = str(row['category']).strip()
                try:
                    price = float(row['price'])
                except (ValueError, TypeError):
                    errors.append(f"Fila {index+2}: Precio inválido '{row['price']}'")
                    continue

                description = str(row.get('description', '')).strip()
                p_type = str(row.get('type', 'physical')).lower().strip()
                if p_type not in ['physical', 'service']:
                    p_type = 'physical'
                
                status_val = str(row.get('status', 'active')).lower().strip()
                if status_val not in ['active', 'paused', 'archived']:
                    status_val = 'active'

                stock = None
                if p_type == 'physical':
                    try:
                        stock = int(row.get('stock', 0))
                    except (ValueError, TypeError):
                        stock = 0

                min_stock = 5
                try:
                    min_stock = int(row.get('min_stock_threshold', 5))
                except (ValueError, TypeError):
                    min_stock = 5

                sla = str(row.get('sla', '')) if p_type == 'service' else None

                existing_p = existing_map.get(name.lower())
                
                if dry_run:
                    preview_data.append({
                        "name": name,
                        "category": category,
                        "price": price,
                        "type": p_type,
                        "status": status_val,
                        "stock": stock,
                        "conflict": "update" if existing_p else "new"
                    })
                    continue

                if existing_p:
                    if conflict_strategy == "skip":
                        skipped_count += 1
                        continue
                    elif conflict_strategy == "update":
                        existing_p.category = category
                        existing_p.price = price
                        existing_p.description = description
                        existing_p.type = p_type
                        existing_p.status = status_val
                        existing_p.stock = stock
                        existing_p.min_stock_threshold = min_stock
                        existing_p.sla = sla
                        session.add(existing_p)
                        updated_count += 1
                else:
                    new_product = Product(
                        user_id=current_user.id,
                        name=name,
                        category=category,
                        price=price,
                        description=description,
                        type=p_type,
                        status=status_val,
                        stock=stock,
                        min_stock_threshold=min_stock,
                        sla=sla
                    )
                    session.add(new_product)
                    imported_count += 1

            except Exception as e:
                errors.append(f"Fila {index+2}: {str(e)}")

        if not dry_run:
            await session.commit()

        return {
            "dry_run": dry_run,
            "total_processed": len(df),
            "imported": imported_count,
            "updated": updated_count,
            "skipped": skipped_count,
            "preview": preview_data if dry_run else None,
            "errors": errors if errors else None
        }
    except HTTPException:
        await session.rollback()
        raise
    except Exception as e:
        await session.rollback()
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
    headers = [
        "name",
        "category",
        "price",
        "stock",
        "description",
        "type",
        "status",
        "min_stock_threshold",
        "sla",
    ]

    sample_rows = [
        [
            "Laptop HP",
            "Hardware",
            "1200",
            "15",
            "Laptop de alto rendimiento",
            "physical",
            "active",
            "5",
            "",
        ],
        [
            "Consultoría Seguridad",
            "Servicios",
            "1500",
            "0",
            "Auditoría de seguridad informática",
            "service",
            "paused",
            "",
            "48h report",
        ],
    ]

    if format == "xlsx":
        buffer = io.BytesIO()
        df = pd.DataFrame(sample_rows, columns=headers)
        df.to_excel(buffer, index=False)
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": 'attachment; filename="plantilla_inventario.xlsx"'
            },
        )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in sample_rows:
        writer.writerow(row)
    contents = output.getvalue().encode("utf-8")
    return StreamingResponse(
        io.BytesIO(contents),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="plantilla_inventario.csv"'},
    )

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
