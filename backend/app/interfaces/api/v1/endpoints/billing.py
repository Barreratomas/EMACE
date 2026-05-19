from typing import Any, Dict
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database.session import get_async_session
from app.domain.models import User
from app.interfaces.api.deps import get_current_user
from app.infrastructure.repositories.billing import BillingRepository
from app.infrastructure.adapters.rate_limit import limiter
from app.application.use_cases.billing_use_cases import BillingUseCases

router = APIRouter()
billing_repo = BillingRepository()
billing_use_cases = BillingUseCases(billing_repo)

@router.get("/access-state")
@limiter.limit("30/minute")
async def get_access_state(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Consulta el estado actual de acceso del vendor (suscripción o lifetime)"""
    return await billing_use_cases.get_access_state(session, current_user)

@router.post("/refresh", status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def refresh_state(
    request: Request,
    body: Dict[str, Any] | None = None,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Sincroniza y actualiza manualmente el estado de facturación desde proveedores externos"""
    billing_use_cases.ensure_vendor(current_user)
    state = await billing_repo.get_access_state(session, current_user.id)
    await billing_repo.save_billing_event(
        session=session,
        vendor_id=current_user.id,
        event_type="refresh_requested",
        mp_event_id=None,
        raw_payload=body or {},
        normalized={"state": {
            "access_mode": getattr(state, "access_mode", None),
            "source": getattr(state, "source", None),
            "valid_until": getattr(state, "valid_until", None),
            "subscription_id_mp": getattr(state, "subscription_id_mp", None),
        }}
    )
    return {
        "status": "ok",
        "state": {
            "access_mode": getattr(state, "access_mode", None),
            "source": getattr(state, "source", None),
            "valid_until": getattr(state, "valid_until", None),
            "subscription_id_mp": getattr(state, "subscription_id_mp", None),
        }
    }


@router.post("/subscriptions", status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_subscription(
    request: Request,
    body: Dict[str, Any],
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Inicia el proceso de creación de una suscripción recurrente en Mercado Pago"""
    return await billing_use_cases.create_subscription(session, current_user, body)

@router.post("/cancel-subscription", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def cancel_subscription(
    request: Request,
    body: Dict[str, Any] | None = None,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Solicita la cancelación de una suscripción activa"""
    return await billing_use_cases.cancel_subscription(session, current_user, body)


@router.post("/lifetime", status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def purchase_lifetime(
    request: Request,
    body: Dict[str, Any],
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """Gestiona la compra de acceso de por vida (Lifetime Access)"""
    billing_use_cases.ensure_vendor(current_user)
    # Lógica de lifetime simplificada aquí o movida a UseCase si es compleja
    from app.infrastructure.config import settings
    import httpx
    state = await billing_repo.get_access_state(session, current_user.id)
    if settings.MP_ACCESS_TOKEN and getattr(state, "subscription_id_mp", None):
        url = f"https://api.mercadopago.com/preapproval/{state.subscription_id_mp}"
        headers = {"Authorization": f"Bearer {settings.MP_ACCESS_TOKEN}"}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.put(url, headers=headers, json={"status": "cancelled"})
        except: pass
    
    updates = {
        "access_mode": "lifetime",
        "source": "lifetime_purchase",
        "valid_until": None,
        "subscription_id_mp": None,
        "_action": "set_lifetime"
    }
    state = await billing_repo.upsert_access_state(session, current_user.id, updates, actor_user_id=current_user.id)
    return {
        "vendor_id": state.vendor_id,
        "access_mode": state.access_mode,
        "source": state.source,
        "valid_until": state.valid_until,
    }
