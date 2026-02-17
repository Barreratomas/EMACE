from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Request
import httpx
import hmac
import hashlib
from asyncio import sleep
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import logging
import time
from app.core.database.session import get_async_session
from app.core.database.models import User, VendorAccessState
from app.core.config import settings
from app.api.deps import get_current_user
from app.repositories.billing import BillingRepository
from app.core.rate_limit import limiter
from app.api.deps import require_access

router = APIRouter()
billing_repo = BillingRepository()
logger = logging.getLogger(__name__)


def ensure_vendor(user: User):
    if user.parent_id is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Solo el Vendor puede gestionar billing")

async def create_mp_preference(vendor_id: int, body: Dict[str, Any]) -> str:
    if not settings.MP_ACCESS_TOKEN:
        return f"https://example.com/checkout/simulated?vendor={vendor_id}"
    item = {
        "title": body.get("title", "Suscripción Mensual"),
        "quantity": 1,
        "unit_price": float(body.get("price", 1.0)),
        "currency_id": body.get("currency_id", settings.MP_CURRENCY_ID),
    }
    payload = {
        "items": body.get("items") or [{
            **item
        }],
        "back_urls": body.get("back_urls") or {
            "success": body.get("success_url", "http://localhost:3000/settings/billing?status=success"),
            "failure": body.get("failure_url", "http://localhost:3000/settings/billing?status=failure"),
            "pending": body.get("pending_url", "http://localhost:3000/settings/billing?status=pending")
        },
        "auto_return": "approved",
        **({"notification_url": settings.MP_WEBHOOK_URL} if settings.MP_WEBHOOK_URL else {}),
        "metadata": {
            "vendor_id": vendor_id
        },
        "external_reference": body.get("external_reference") or f"vendor-{vendor_id}-{uuid4()}",
    }
    headers = {
        "Authorization": f"Bearer {settings.MP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Idempotency-Key": body.get("idempotency_key") or str(uuid4())
    }
    timeout = httpx.Timeout(10.0, read=20.0)
    retries = 3
    last_exc: Exception | None = None
    url = "https://api.mercadopago.com/checkout/preferences"
    for attempt in range(retries):
        try:
            t0 = time.perf_counter()
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(url, json=payload, headers=headers)
            latency_ms = int((time.perf_counter() - t0) * 1000)
            if resp.status_code >= 200 and resp.status_code < 300:
                data = resp.json()
                logger.info({
                    "event": "mp.preference.create",
                    "status": "success",
                    "http_status": resp.status_code,
                    "latency_ms": latency_ms,
                    "vendor_id": vendor_id,
                })
                return data.get("init_point") or data.get("sandbox_init_point") or ""
            # Retry on 5xx
            if 500 <= resp.status_code < 600:
                logger.warning({
                    "event": "mp.preference.create",
                    "status": "retrying",
                    "http_status": resp.status_code,
                    "attempt": attempt + 1,
                    "vendor_id": vendor_id,
                })
                await sleep(0.5 * (2 ** attempt))
                continue
            # Non-retryable
            err_detail = None
            try:
                j = resp.json()
                err_detail = j.get("message") or j.get("error") or j
            except Exception:
                err_detail = resp.text
            logger.error({
                "event": "mp.preference.create",
                "status": "error",
                "http_status": resp.status_code,
                "detail": str(err_detail)[:500],
                "vendor_id": vendor_id,
            })
            raise HTTPException(status_code=resp.status_code, detail=f"MP error: {str(err_detail)[:300]}")
        except httpx.HTTPError as e:
            last_exc = e
            logger.error({
                "event": "mp.preference.create",
                "status": "exception",
                "attempt": attempt + 1,
                "error": str(e),
                "vendor_id": vendor_id,
            })
            await sleep(0.5 * (2 ** attempt))
    raise HTTPException(status_code=502, detail=f"No se pudo crear preferencia en Mercado Pago: {last_exc}")

@router.get("/access-state")
@limiter.limit("30/minute")
async def get_access_state(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    ensure_vendor(current_user)
    state = await billing_repo.get_access_state(session, current_user.id)
    if not state:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Estado de acceso no encontrado")
    return {
        "vendor_id": state.vendor_id,
        "access_mode": state.access_mode,
        "source": state.source,
        "valid_until": state.valid_until,
        "subscription_id_mp": state.subscription_id_mp
    }

@router.post("/refresh", status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def refresh_state(
    request: Request,
    body: Dict[str, Any] | None = None,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    ensure_vendor(current_user)
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
    ensure_vendor(current_user)
    checkout_url = await create_mp_preference(current_user.id, body or {})

    await billing_repo.save_billing_event(
        session=session,
        vendor_id=current_user.id,
        event_type="subscription_create_requested",
        mp_event_id=None,
        raw_payload={"request": body},
        normalized={"checkout_url": checkout_url}
    )
    logger.info({
        "event": "subscription.create.requested",
        "vendor_id": current_user.id,
        "checkout_url": "redacted" if "mercadopago.com" in checkout_url else checkout_url
    })
    return {"checkout_url": checkout_url}

@router.post("/cancel-subscription", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def cancel_subscription(
    request: Request,
    body: Dict[str, Any] | None = None,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    ensure_vendor(current_user)
    state = await billing_repo.get_access_state(session, current_user.id)
    if not state or state.access_mode != "subscription":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No hay suscripción activa para cancelar")
    # Intento best-effort de cancelar en MP si tenemos ID y token
    if settings.MP_ACCESS_TOKEN and state.subscription_id_mp:
        url = f"https://api.mercadopago.com/preapproval/{state.subscription_id_mp}"
        headers = {
            "Authorization": f"Bearer {settings.MP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.put(url, headers=headers, json={"status": "cancelled"})
        except httpx.HTTPError:
            # Continuar igualmente; la política conserva acceso hasta valid_until
            pass
    updates = {
        "subscription_id_mp": None,
        "_action": "cancel_subscription"
    }
    state = await billing_repo.upsert_access_state(session, current_user.id, updates, actor_user_id=current_user.id)
    await billing_repo.save_billing_event(
        session=session,
        vendor_id=current_user.id,
        event_type="subscription_cancel_requested",
        mp_event_id=None,
        raw_payload=body or {},
        normalized={"valid_until": state.valid_until}
    )
    return {"status": "ok", "valid_until": state.valid_until}


@router.post("/lifetime", status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def purchase_lifetime(
    request: Request,
    body: Dict[str, Any],
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    ensure_vendor(current_user)
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


def verify_mp_signature(request: Request, body: bytes) -> bool:
    secret = settings.MP_WEBHOOK_SECRET
    if not secret:
        return True
    sig_header = request.headers.get("x-signature") or request.headers.get("X-Signature")
    if not sig_header:
        return False
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    candidate = sig_header.strip().lower()
    return hmac.compare_digest(digest, candidate)


@router.post("/webhooks/mp", status_code=status.HTTP_200_OK)
async def mercado_pago_webhook(
    request: Request,
    payload: Dict[str, Any],
    session: AsyncSession = Depends(get_async_session)
):
    raw = await request.body()
    if not verify_mp_signature(request, raw):
        logger.warning({"event": "mp.webhook.signature_invalid"})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Firma inválida")

    mp_event_id = request.headers.get("x-request-id") or str(payload.get("id") or payload.get("data", {}).get("id") or "")
    if mp_event_id:
        existing = await billing_repo.find_event_by_mp_id(session, mp_event_id)
        if existing:
            logger.info({"event": "mp.webhook.idempotent", "mp_event_id": mp_event_id})
            return {"status": "ok", "idempotent": True}

    topic = payload.get("type") or payload.get("topic") or "unknown"
    vendor_id = payload.get("metadata", {}).get("vendor_id") or payload.get("vendor_id")

    if vendor_id is None:
        await billing_repo.save_billing_event(session, vendor_id=0, event_type="unassigned_event", mp_event_id=mp_event_id, raw_payload=payload, normalized=None)
        logger.info({"event": "mp.webhook.unassigned", "topic": topic, "mp_event_id": mp_event_id})
        return {"status": "ok"}

    if topic in ("payment", "subscription_paid", "payment.updated"):
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        updates = {
            "access_mode": "subscription",
            "source": "paid_subscription",
            "valid_until": now + timedelta(days=30),
            "_action": "extend_subscription"
        }
        await billing_repo.upsert_access_state(session, int(vendor_id), updates)
        await billing_repo.save_billing_event(session, vendor_id=int(vendor_id), event_type="subscription_renewed", mp_event_id=mp_event_id, raw_payload=payload, normalized=updates)
        logger.info({"event": "mp.webhook.payment_approved", "vendor_id": int(vendor_id)})
    elif topic in ("payment_failed", "subscription_past_due"):
        updates = {"_action": "mark_past_due"}
        await billing_repo.save_billing_event(session, vendor_id=int(vendor_id), event_type="subscription_past_due", mp_event_id=mp_event_id, raw_payload=payload, normalized=updates)
        logger.info({"event": "mp.webhook.payment_failed", "vendor_id": int(vendor_id)})
    else:
        await billing_repo.save_billing_event(session, vendor_id=int(vendor_id), event_type=topic, mp_event_id=mp_event_id, raw_payload=payload, normalized=None)
        logger.info({"event": "mp.webhook.other", "topic": topic, "vendor_id": int(vendor_id)})

    return {"status": "ok"}

@router.get("/webhooks/mp/health", status_code=status.HTTP_200_OK)
async def webhook_health():
    return {"status": "ok"}

@router.get("/metrics-admin")
@limiter.limit("5/minute")
async def metrics_admin(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    if not current_user.role or current_user.role.name != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Se requieren privilegios de administrador")
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    trials_active_q = await session.execute(
        select(VendorAccessState).where(
            and_(VendorAccessState.source == "trial", VendorAccessState.valid_until != None, VendorAccessState.valid_until > now)
        )
    )
    trials_expired_q = await session.execute(
        select(VendorAccessState).where(
            and_(VendorAccessState.source == "trial", VendorAccessState.valid_until != None, VendorAccessState.valid_until <= now)
        )
    )
    subs_active_q = await session.execute(
        select(VendorAccessState).where(
            and_(VendorAccessState.source == "paid_subscription", VendorAccessState.valid_until != None, VendorAccessState.valid_until > now)
        )
    )
    subs_past_due_q = await session.execute(
        select(VendorAccessState).where(
            and_(VendorAccessState.source == "paid_subscription", VendorAccessState.valid_until != None, VendorAccessState.valid_until <= now)
        )
    )
    lifetime_q = await session.execute(
        select(VendorAccessState).where(VendorAccessState.access_mode == "lifetime")
    )
    res = {
        "trials_active": len(trials_active_q.scalars().all()),
        "trials_expired": len(trials_expired_q.scalars().all()),
        "subs_active": len(subs_active_q.scalars().all()),
        "subs_past_due": len(subs_past_due_q.scalars().all()),
        "lifetime": len(lifetime_q.scalars().all()),
    }
    logger.info({"event": "billing.metrics_admin.requested", "by": current_user.id})
    return res
