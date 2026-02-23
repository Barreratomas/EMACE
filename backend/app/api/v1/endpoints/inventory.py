from typing import List, Optional
import io
import csv
from datetime import datetime, timedelta, timezone
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile, File, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database.session import get_async_session
from app.core.database.models import (
    Product,
    ProductUpdate,
    User,
    Customer,
    Invoice,
    AuditLog,
    Order,
)
from app.core.rate_limit import limiter
from app.core.config import settings
from app.repositories.product import product_repo
from sqlmodel import Session
from app.core.database.session import engine
from app.api.deps import get_current_user, get_tenant_owner_id
from sqlalchemy import select, func

router = APIRouter()
dashboard_router = APIRouter()
agents_router = APIRouter()
analytics_router = APIRouter()
platform_router = APIRouter()

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


class DashboardStat(BaseModel):
    key: str
    label: str
    value: str
    trend: Optional[str] = None
    trend_direction: Optional[str] = None


class DashboardAgentSummary(BaseModel):
    name: str
    status: str
    load: int
    activity: Optional[str] = None
    type: Optional[str] = None


class DashboardChartPoint(BaseModel):
    timestamp: datetime
    total_events: int


class DashboardOverviewResponse(BaseModel):
    stats: List[DashboardStat]
    agents: List[DashboardAgentSummary]
    chart_24h: List[DashboardChartPoint]


class DashboardActivityItem(BaseModel):
    id: int
    type: str
    message: str
    timestamp: datetime


class AgentCatalogItem(BaseModel):
    id: str
    name: str
    role: str
    domain: str
    status: str
    load: int
    latency: str


class AgentToolItem(BaseModel):
    key: str
    label: str
    agents: List[str]
    icon: str


class AgentEventItem(BaseModel):
    timestamp: datetime
    level: str
    agent_name: str
    action: str
    details: str


class MetricItem(BaseModel):
    key: str
    label: str
    value: str
    trend: Optional[str] = None


class AuditStreamItem(BaseModel):
    timestamp: datetime
    level: str
    category: str
    message: str


class PlatformFeatureFlag(BaseModel):
    key: str
    name: str
    enabled: bool
    status: str
    reason: Optional[str] = None


class PlatformFeaturesResponse(BaseModel):
    features: List[PlatformFeatureFlag]


AGENT_CATALOG = [
    {
        "id": "general",
        "name": "EMACE_CORE",
        "role": "Orquestador General",
        "status": "online",
        "load": 42,
        "latency": "1.2s",
        "domain": "Core Routing",
    },
    {
        "id": "inventory",
        "name": "AGENTE_INVENTARIO",
        "role": "Stock y Catálogo",
        "status": "online",
        "load": 68,
        "latency": "1.5s",
        "domain": "Inventory",
    },
    {
        "id": "sales",
        "name": "AGENTE_VENTAS",
        "role": "Pedidos y Clientes",
        "status": "busy",
        "load": 83,
        "latency": "2.1s",
        "domain": "Sales",
    },
    {
        "id": "logistics",
        "name": "AGENTE_LOGISTICA",
        "role": "Rutas y Entregas",
        "status": "online",
        "load": 37,
        "latency": "1.0s",
        "domain": "Logistics",
    },
]


AGENT_TOOLS = [
    {
        "key": "inventory",
        "label": "Inventario",
        "agents": ["AGENTE_INVENTARIO"],
        "icon": "Database",
    },
    {
        "key": "sales",
        "label": "Ventas",
        "agents": ["AGENTE_VENTAS"],
        "icon": "Network",
    },
    {
        "key": "logistics",
        "label": "Logística",
        "agents": ["AGENTE_LOGISTICA"],
        "icon": "Cpu",
    },
]


@dashboard_router.get("/overview", response_model=DashboardOverviewResponse)
@limiter.limit(settings.RATE_LIMIT_READ_PRODUCTS)
async def get_vendor_dashboard_overview(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    tenant_id = get_tenant_owner_id(current_user)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    since_24h = now - timedelta(hours=24)
    since_30d = now - timedelta(days=30)

    stats: List[DashboardStat] = []

    products_result = await session.execute(
        select(func.count(Product.id)).where(
            Product.user_id == tenant_id,
            Product.status == "active",
        )
    )
    products_total = products_result.scalar() or 0
    stats.append(
        DashboardStat(
            key="products_active",
            label="Productos activos",
            value=str(products_total),
        )
    )

    customers_result = await session.execute(
        select(func.count(Customer.id)).where(Customer.user_id == tenant_id)
    )
    customers_total = customers_result.scalar() or 0
    stats.append(
        DashboardStat(
            key="customers_total",
            label="Clientes",
            value=str(customers_total),
        )
    )

    invoices_result = await session.execute(
        select(
            func.count(Invoice.id),
            func.coalesce(func.sum(Invoice.amount), 0.0),
        ).where(
            Invoice.user_id == tenant_id,
            Invoice.status == "paid",
            Invoice.issued_at >= since_30d,
        )
    )
    invoices_row = invoices_result.first()
    invoices_count = 0
    invoices_amount = 0.0
    if invoices_row:
        invoices_count = invoices_row[0] or 0
        invoices_amount = float(invoices_row[1] or 0.0)
    stats.append(
        DashboardStat(
            key="invoices_paid_30d",
            label="Facturas pagadas (30d)",
            value=f"{invoices_count} / {invoices_amount:.2f}",
        )
    )

    operations_result = await session.execute(
        select(func.count(AuditLog.id)).where(
            AuditLog.user_id == tenant_id,
            AuditLog.timestamp >= since_24h,
        )
    )
    operations_total = operations_result.scalar() or 0
    stats.append(
        DashboardStat(
            key="operations_24h",
            label="Operaciones 24h",
            value=str(operations_total),
        )
    )

    agents: List[DashboardAgentSummary] = []
    agents_result = await session.execute(
        select(
            AuditLog.agent_name,
            func.count(AuditLog.id),
            func.max(AuditLog.timestamp),
        )
        .where(
            AuditLog.user_id == tenant_id,
            AuditLog.timestamp >= since_24h,
        )
        .group_by(AuditLog.agent_name)
    )
    agent_rows = agents_result.all()
    max_events = max((row[1] for row in agent_rows), default=0)
    for agent_name, event_count, last_ts in agent_rows:
        load = int((event_count / max_events) * 100) if max_events > 0 else 0
        status_label = "Offline"
        if last_ts:
            if last_ts >= now - timedelta(minutes=15):
                status_label = "Online"
                if load > 70:
                    status_label = "Busy"
        activity_label = None
        if last_ts:
            delta = now - last_ts
            if delta.days >= 1:
                activity_label = f"Hace {delta.days}d"
            else:
                hours = delta.seconds // 3600
                minutes = (delta.seconds % 3600) // 60
                if hours > 0:
                    activity_label = f"Hace {hours}h"
                elif minutes > 0:
                    activity_label = f"Hace {minutes}m"
                else:
                    activity_label = "Hace segundos"
        agent_type = "System"
        upper_name = agent_name.upper()
        if "VENTAS" in upper_name:
            agent_type = "Client"
        elif "LOGISTICA" in upper_name:
            agent_type = "Core"
        elif "ANALITICA" in upper_name:
            agent_type = "Service"
        agents.append(
            DashboardAgentSummary(
                name=agent_name,
                status=status_label,
                load=load,
                activity=activity_label,
                type=agent_type,
            )
        )

    chart_points: List[DashboardChartPoint] = []
    audit_result = await session.execute(
        select(AuditLog.timestamp).where(
            AuditLog.user_id == tenant_id,
            AuditLog.timestamp >= since_24h,
        )
    )
    timestamps = audit_result.scalars().all()
    bucket_counts = {}
    for ts in timestamps:
        bucket_ts = ts.replace(minute=0, second=0, microsecond=0)
        key = bucket_ts
        bucket_counts[key] = bucket_counts.get(key, 0) + 1
    start_bucket = since_24h.replace(minute=0, second=0, microsecond=0)
    for i in range(24):
        bucket_ts = start_bucket + timedelta(hours=i)
        count = bucket_counts.get(bucket_ts, 0)
        chart_points.append(
            DashboardChartPoint(
                timestamp=bucket_ts,
                total_events=count,
            )
        )

    overview = DashboardOverviewResponse(
        stats=stats,
        agents=agents,
        chart_24h=chart_points,
    )
    return overview


@dashboard_router.get("/activity/recent", response_model=List[DashboardActivityItem])
@limiter.limit(settings.RATE_LIMIT_READ_PRODUCTS)
async def get_vendor_recent_activity(
    request: Request,
    limit: int = 20,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    tenant_id = get_tenant_owner_id(current_user)
    result = await session.execute(
        select(AuditLog)
        .where(AuditLog.user_id == tenant_id)
        .order_by(AuditLog.timestamp.desc())
        .limit(limit)
    )
    logs = result.scalars().all()
    items: List[DashboardActivityItem] = []
    for log in logs:
        level = "info"
        lower_action = (log.action or "").lower()
        if "error" in lower_action or "fail" in lower_action or "exception" in lower_action:
            level = "error"
        elif "warn" in lower_action or "high_load" in lower_action:
            level = "warning"
        elif "success" in lower_action or "ok" in lower_action or "complete" in lower_action:
            level = "success"
        text = log.details or log.action or ""
        items.append(
            DashboardActivityItem(
                id=log.id or 0,
                type=level,
                message=text,
                timestamp=log.timestamp,
            )
        )
    return items


@agents_router.get("/agents", response_model=List[AgentCatalogItem])
@limiter.limit(settings.RATE_LIMIT_READ_PRODUCTS)
async def get_vendor_agents_catalog(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    tenant_id = get_tenant_owner_id(current_user)
    _ = tenant_id
    return [AgentCatalogItem(**item) for item in AGENT_CATALOG]


@agents_router.get("/agents/tools", response_model=List[AgentToolItem])
@limiter.limit(settings.RATE_LIMIT_READ_PRODUCTS)
async def get_vendor_agents_tools(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    tenant_id = get_tenant_owner_id(current_user)
    _ = tenant_id
    return [AgentToolItem(**item) for item in AGENT_TOOLS]


@agents_router.get("/agents/events", response_model=List[AgentEventItem])
@limiter.limit(settings.RATE_LIMIT_READ_PRODUCTS)
async def get_vendor_agents_events(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    tenant_id = get_tenant_owner_id(current_user)
    result = await session.execute(
        select(AuditLog)
        .where(AuditLog.user_id == tenant_id)
        .order_by(AuditLog.timestamp.desc())
        .offset(offset)
        .limit(limit)
    )
    logs = result.scalars().all()
    events: List[AgentEventItem] = []
    for log in logs:
        level = "INFO"
        lower_action = (log.action or "").lower()
        if "error" in lower_action or "fail" in lower_action or "exception" in lower_action:
            level = "ERROR"
        elif "warn" in lower_action or "high_load" in lower_action:
            level = "WARN"
        elif "success" in lower_action or "ok" in lower_action or "complete" in lower_action:
            level = "OK"
        events.append(
            AgentEventItem(
                timestamp=log.timestamp,
                level=level,
                agent_name=log.agent_name,
                action=log.action,
                details=log.details,
            )
        )
    return events


@analytics_router.get("/metrics/system", response_model=List[MetricItem])
@limiter.limit(settings.RATE_LIMIT_READ_PRODUCTS)
async def get_vendor_system_metrics(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    tenant_id = get_tenant_owner_id(current_user)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    since_24h = now - timedelta(hours=24)
    since_7d = now - timedelta(days=7)
    metrics: List[MetricItem] = []
    operations_24h_result = await session.execute(
        select(func.count(AuditLog.id)).where(
            AuditLog.user_id == tenant_id,
            AuditLog.timestamp >= since_24h,
        )
    )
    operations_24h = operations_24h_result.scalar() or 0
    metrics.append(
        MetricItem(
            key="system_operations_24h",
            label="Operaciones últimas 24h",
            value=str(operations_24h),
            trend=None,
        )
    )
    agents_active_result = await session.execute(
        select(func.count(func.distinct(AuditLog.agent_name))).where(
            AuditLog.user_id == tenant_id,
            AuditLog.timestamp >= since_24h,
        )
    )
    agents_active = agents_active_result.scalar() or 0
    metrics.append(
        MetricItem(
            key="system_agents_active_24h",
            label="Agentes activos 24h",
            value=str(agents_active),
            trend=None,
        )
    )
    logs_7d_result = await session.execute(
        select(func.count(AuditLog.id)).where(
            AuditLog.user_id == tenant_id,
            AuditLog.timestamp >= since_7d,
        )
    )
    logs_7d = logs_7d_result.scalar() or 0
    metrics.append(
        MetricItem(
            key="system_audit_logs_7d",
            label="Eventos últimos 7d",
            value=str(logs_7d),
            trend=None,
        )
    )
    return metrics


@analytics_router.get("/metrics/inventory", response_model=List[MetricItem])
@limiter.limit(settings.RATE_LIMIT_READ_PRODUCTS)
async def get_vendor_inventory_metrics(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    tenant_id = get_tenant_owner_id(current_user)
    metrics: List[MetricItem] = []
    products_result = await session.execute(
        select(func.count(Product.id)).where(
            Product.user_id == tenant_id,
            Product.status == "active",
        )
    )
    products_total = products_result.scalar() or 0
    metrics.append(
        MetricItem(
            key="inventory_products_active",
            label="Productos activos",
            value=str(products_total),
            trend=None,
        )
    )
    low_stock_result = await session.execute(
        select(func.count(Product.id)).where(
            Product.user_id == tenant_id,
            Product.type == "physical",
            Product.stock.is_not(None),
            Product.stock <= func.coalesce(Product.min_stock_threshold, 5),
        )
    )
    low_stock = low_stock_result.scalar() or 0
    metrics.append(
        MetricItem(
            key="inventory_low_stock_items",
            label="Productos con stock bajo",
            value=str(low_stock),
            trend=None,
        )
    )
    categories_result = await session.execute(
        select(func.count(func.distinct(Product.category))).where(
            Product.user_id == tenant_id,
        )
    )
    categories_total = categories_result.scalar() or 0
    metrics.append(
        MetricItem(
            key="inventory_categories",
            label="Categorías de producto",
            value=str(categories_total),
            trend=None,
        )
    )
    inventory_value_result = await session.execute(
        select(
            func.coalesce(
                func.sum(
                    Product.price * func.coalesce(Product.stock, 0)
                ),
                0.0,
            )
        ).where(
            Product.user_id == tenant_id,
            Product.type == "physical",
            Product.stock.is_not(None),
        )
    )
    inventory_value = float(inventory_value_result.scalar() or 0.0)
    metrics.append(
        MetricItem(
            key="inventory_value_estimated",
            label="Valor inventario estimado",
            value=f"{inventory_value:.2f}",
            trend=None,
        )
    )
    return metrics


@analytics_router.get("/metrics/business", response_model=List[MetricItem])
@limiter.limit(settings.RATE_LIMIT_READ_PRODUCTS)
async def get_vendor_business_metrics(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    tenant_id = get_tenant_owner_id(current_user)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    since_30d = now - timedelta(days=30)
    metrics: List[MetricItem] = []
    invoices_result = await session.execute(
        select(
            func.count(Invoice.id),
            func.coalesce(func.sum(Invoice.amount), 0.0),
        ).where(
            Invoice.user_id == tenant_id,
            Invoice.status == "paid",
            Invoice.issued_at >= since_30d,
        )
    )
    invoices_row = invoices_result.first()
    invoices_count = 0
    invoices_amount = 0.0
    if invoices_row:
        invoices_count = invoices_row[0] or 0
        invoices_amount = float(invoices_row[1] or 0.0)
    metrics.append(
        MetricItem(
            key="business_invoices_paid_30d",
            label="Facturas pagadas 30d",
            value=str(invoices_count),
            trend=None,
        )
    )
    metrics.append(
        MetricItem(
            key="business_revenue_30d",
            label="Ingresos 30d",
            value=f"{invoices_amount:.2f}",
            trend=None,
        )
    )
    customers_result = await session.execute(
        select(func.count(Customer.id)).where(Customer.user_id == tenant_id)
    )
    customers_total = customers_result.scalar() or 0
    metrics.append(
        MetricItem(
            key="business_customers_total",
            label="Clientes totales",
            value=str(customers_total),
            trend=None,
        )
    )
    orders_result = await session.execute(
        select(func.count(Order.id)).where(
            Order.user_id == tenant_id,
            Order.created_at >= since_30d,
        )
    )
    orders_total = orders_result.scalar() or 0
    metrics.append(
        MetricItem(
            key="business_orders_30d",
            label="Pedidos 30d",
            value=str(orders_total),
            trend=None,
        )
    )
    return metrics


@analytics_router.get("/audit/stream", response_model=List[AuditStreamItem])
@limiter.limit(settings.RATE_LIMIT_READ_PRODUCTS)
async def get_vendor_audit_stream(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    category: Optional[str] = Query(default=None),
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    tenant_id = get_tenant_owner_id(current_user)
    base_limit = limit + offset
    result = await session.execute(
        select(AuditLog)
        .where(AuditLog.user_id == tenant_id)
        .order_by(AuditLog.timestamp.desc())
        .limit(base_limit * 2)
    )
    logs = result.scalars().all()
    items: List[AuditStreamItem] = []
    category_filter = category.upper() if category else None
    for log in logs:
        text = (log.action or "") + " " + (log.details or "")
        lower_text = text.lower()
        derived_category = "SYSTEM"
        if "stock" in lower_text or "inventory" in lower_text or "product" in lower_text:
            derived_category = "INVENTORY"
        elif "sale" in lower_text or "order" in lower_text or "invoice" in lower_text:
            derived_category = "BUSINESS"
        elif "auth" in lower_text or "login" in lower_text or "register" in lower_text:
            derived_category = "AUTH"
        elif "latency" in lower_text or "network" in lower_text:
            derived_category = "NETWORK"
        elif "memory" in lower_text or "vector" in lower_text:
            derived_category = "MEMORY"
        elif log.agent_name:
            derived_category = "AGENT"
        level = "INFO"
        if "error" in lower_text or "fail" in lower_text or "exception" in lower_text:
            level = "ERROR"
        elif "warn" in lower_text or "high_load" in lower_text:
            level = "WARN"
        elif "success" in lower_text or "ok" in lower_text or "complete" in lower_text:
            level = "SUCCESS"
        if category_filter and derived_category != category_filter:
            continue
        message = log.details or log.action or ""
        items.append(
            AuditStreamItem(
                timestamp=log.timestamp,
                level=level,
                category=derived_category,
                message=message,
            )
        )
    sliced = items[offset : offset + limit]
    return sliced


@platform_router.get("/features", response_model=PlatformFeaturesResponse)
@limiter.limit(settings.RATE_LIMIT_HEALTH)
async def get_platform_features(
    request: Request,
):
    features: List[PlatformFeatureFlag] = []

    billing_enabled = bool(settings.MP_ACCESS_TOKEN)
    billing_status = "ok" if billing_enabled else "disabled"
    billing_reason = None
    if not billing_enabled:
        billing_reason = "Integración de Mercado Pago no configurada"
    features.append(
        PlatformFeatureFlag(
            key="billing",
            name="Módulo de Facturación",
            enabled=billing_enabled,
            status=billing_status,
            reason=billing_reason,
        )
    )

    notifications_enabled = bool(settings.SMTP_ENABLED or settings.TELEGRAM_ENABLED)
    notifications_status = "ok" if notifications_enabled else "disabled"
    notifications_reason = None
    if not notifications_enabled:
        notifications_reason = "SMTP y Telegram desactivados"
    features.append(
        PlatformFeatureFlag(
            key="notifications",
            name="Notificaciones",
            enabled=notifications_enabled,
            status=notifications_status,
            reason=notifications_reason,
        )
    )

    integrations_enabled = bool(
        settings.TELEGRAM_ENABLED
        or settings.TELEGRAM_MTPROTO_ENABLED
        or settings.MP_ACCESS_TOKEN
    )
    integrations_status = "ok" if integrations_enabled else "partial"
    integrations_reason = None
    if not integrations_enabled:
        integrations_reason = "Sin integraciones externas configuradas"
    features.append(
        PlatformFeatureFlag(
            key="integrations",
            name="Integraciones externas",
            enabled=integrations_enabled,
            status=integrations_status,
            reason=integrations_reason,
        )
    )

    features.append(
        PlatformFeatureFlag(
            key="low_latency_api",
            name="API de baja latencia",
            enabled=True,
            status="ok",
            reason=None,
        )
    )
    features.append(
        PlatformFeatureFlag(
            key="encryption",
            name="Cifrado y seguridad",
            enabled=True,
            status="ok",
            reason=None,
        )
    )

    return PlatformFeaturesResponse(features=features)
