from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
import httpx
import hmac
import hashlib
from asyncio import sleep
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import logging
import time
import re
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

    # Deducir base URL (preferiblemente el túnel si está configurado)
    base_url = "http://localhost:3000"
    if settings.MP_WEBHOOK_URL and "trycloudflare.com" in settings.MP_WEBHOOK_URL:
        # Extraer https://dominio.trycloudflare.com de la URL completa del webhook
        parts = settings.MP_WEBHOOK_URL.split("/api/v1")
        if len(parts) > 0:
            base_url = parts[0]

    item = {
        "title": body.get("title", "Suscripción Mensual"),
        "quantity": 1,
        "unit_price": float(body.get("price", 1.0)),
        "currency_id": body.get("currency_id", settings.MP_CURRENCY_ID),
    }

    # Construcción robusta de back_urls
    input_back_urls = body.get("back_urls", {})
    # Cuando usamos túnel hacia backend, redirigimos a ruta propia y desde allí al frontend
    if "trycloudflare.com" in base_url:
        success_url = input_back_urls.get("success") or f"{base_url}/api/v1/billing/return?status=success"
        failure_url = input_back_urls.get("failure") or f"{base_url}/api/v1/billing/return?status=failure"
        pending_url = input_back_urls.get("pending") or f"{base_url}/api/v1/billing/return?status=pending"
    else:
        success_url = input_back_urls.get("success") or body.get("success_url") or f"{base_url}/settings/billing?status=success"
        failure_url = input_back_urls.get("failure") or body.get("failure_url") or f"{base_url}/settings/billing?status=failure"
        pending_url = input_back_urls.get("pending") or body.get("pending_url") or f"{base_url}/settings/billing?status=pending"

    payload = {
        "items": body.get("items") or [{**item}],
        "back_urls": {
            "success": success_url,
            "failure": failure_url,
            "pending": pending_url
        },
        "auto_return": "all",  # Cambiado a 'all' para mejor compatibilidad
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

async def create_mp_lifetime_preference(vendor_id: int, body: Dict[str, Any]) -> str:
    if not settings.MP_ACCESS_TOKEN:
        return f"https://example.com/checkout/lifetime?vendor={vendor_id}"
    base_url = "http://localhost:3000"
    if settings.MP_WEBHOOK_URL and "trycloudflare.com" in settings.MP_WEBHOOK_URL:
        parts = settings.MP_WEBHOOK_URL.split("/api/v1")
        if len(parts) > 0:
            base_url = parts[0]
    item = {
        "title": body.get("title", "Acceso de por vida"),
        "quantity": 1,
        "unit_price": float(body.get("price", 1.0)),
        "currency_id": body.get("currency_id", settings.MP_CURRENCY_ID),
    }
    input_back_urls = body.get("back_urls", {})
    if "trycloudflare.com" in base_url:
        success_url = input_back_urls.get("success") or f"{base_url}/api/v1/billing/return?status=success"
        failure_url = input_back_urls.get("failure") or f"{base_url}/api/v1/billing/return?status=failure"
        pending_url = input_back_urls.get("pending") or f"{base_url}/api/v1/billing/return?status=pending"
    else:
        success_url = input_back_urls.get("success") or body.get("success_url") or f"{base_url}/settings/billing?status=success"
        failure_url = input_back_urls.get("failure") or body.get("failure_url") or f"{base_url}/settings/billing?status=failure"
        pending_url = input_back_urls.get("pending") or body.get("pending_url") or f"{base_url}/settings/billing?status=pending"
    payload = {
        "items": body.get("items") or [{**item}],
        "back_urls": {
            "success": success_url,
            "failure": failure_url,
            "pending": pending_url
        },
        "auto_return": "all",
        **({"notification_url": settings.MP_WEBHOOK_URL} if settings.MP_WEBHOOK_URL else {}),
        "metadata": {
            "vendor_id": vendor_id,
            "mode": "lifetime"
        },
        "external_reference": body.get("external_reference") or f"vendor-{vendor_id}-lifetime-{uuid4()}",
    }
    headers = {
        "Authorization": f"Bearer {settings.MP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Idempotency-Key": body.get("idempotency_key") or str(uuid4())
    }
    timeout = httpx.Timeout(10.0, read=20.0)
    url = "https://api.mercadopago.com/checkout/preferences"
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, json=payload, headers=headers)
    if 200 <= resp.status_code < 300:
        data = resp.json()
        return data.get("init_point") or data.get("sandbox_init_point") or ""
    err_detail = None
    try:
        j = resp.json()
        err_detail = j.get("message") or j.get("error") or j
    except Exception:
        err_detail = resp.text
    raise HTTPException(status_code=resp.status_code, detail=f"MP error: {str(err_detail)[:300]}")
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
        await billing_repo.save_billing_event(
            session=session,
            vendor_id=current_user.id,
            event_type="access_state_missing",
            mp_event_id=None,
            raw_payload={},
            normalized=None
        )
        return {
            "vendor_id": current_user.id,
            "access_mode": None,
            "source": "uninitialized",
            "valid_until": None,
            "subscription_id_mp": None
        }
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
    
    # Validar estado de acceso actual
    state = await billing_repo.get_access_state(session, current_user.id)
    if state:
        if state.access_mode == "lifetime":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya posees acceso de por vida. No es necesario suscribirse."
            )
        
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if state.access_mode == "subscription" and state.valid_until and state.valid_until > now:
            # Permitir renovar solo si faltan menos de 7 días para el vencimiento
            if state.valid_until > now + timedelta(days=7):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Ya tienes una suscripción activa hasta el {state.valid_until.strftime('%d/%m/%Y')}. Podrás renovarla 7 días antes de su vencimiento."
                )

    checkout_url = await create_mp_preference(current_user.id, body or {})

    await billing_repo.save_billing_event(
        session=session,
        vendor_id=current_user.id,
        event_type="subscription_create_requested",
        mp_event_id=None,
        raw_payload={"request": body},
        normalized={"checkout_url": checkout_url}
    )

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
    state = await billing_repo.get_access_state(session, current_user.id)
    if settings.MP_ACCESS_TOKEN and getattr(state, "subscription_id_mp", None):
        url = f"https://api.mercadopago.com/preapproval/{state.subscription_id_mp}"
        headers = {
            "Authorization": f"Bearer {settings.MP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.put(url, headers=headers, json={"status": "cancelled"})
        except httpx.HTTPError:
            pass
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
@router.post("/lifetime/checkout", status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def lifetime_checkout(
    request: Request,
    body: Dict[str, Any],
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    ensure_vendor(current_user)
    state = await billing_repo.get_access_state(session, current_user.id)
    if state and state.access_mode == "lifetime":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ya posees acceso de por vida.")
    checkout_url = await create_mp_lifetime_preference(current_user.id, body or {})
    await billing_repo.save_billing_event(
        session=session,
        vendor_id=current_user.id,
        event_type="lifetime_checkout_requested",
        mp_event_id=None,
        raw_payload={"request": body},
        normalized={"checkout_url": checkout_url}
    )
    return {"checkout_url": checkout_url}


def verify_mp_signature(request: Request, body: bytes) -> bool:
    secret = settings.MP_WEBHOOK_SECRET
    tok = settings.MP_ACCESS_TOKEN or ""
    if tok.startswith("APP_USR-") or tok.startswith("TEST-"):
        return True
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
            return {"status": "ok", "idempotent": True}

    topic = payload.get("type") or payload.get("topic") or "unknown"
    vendor_id = payload.get("metadata", {}).get("vendor_id") or payload.get("vendor_id")
    event_id = payload.get("id") or payload.get("data", {}).get("id") or request.query_params.get("id") or request.query_params.get("data.id")
    mode_meta = payload.get("metadata", {}).get("mode")
    if vendor_id is None and settings.MP_ACCESS_TOKEN and event_id:
        try:
            headers = {"Authorization": f"Bearer {settings.MP_ACCESS_TOKEN}"}
            async with httpx.AsyncClient(timeout=10.0) as client:
                if topic in ("payment", "payment.updated"):
                    r = await client.get(f"https://api.mercadopago.com/v1/payments/{event_id}", headers=headers)
                    if r.status_code == 200:
                        d = r.json()
                        vendor_id = d.get("metadata", {}).get("vendor_id")
                        mode_meta = mode_meta or d.get("metadata", {}).get("mode")
                        if vendor_id is None:
                            ext = d.get("external_reference") or ""
                            m = re.search(r"vendor-(\d+)-", ext)
                            if m:
                                vendor_id = int(m.group(1))
                            if "lifetime" in ext:
                                mode_meta = "lifetime"
                elif topic in ("merchant_order",):
                    r = await client.get(f"https://api.mercadopago.com/merchant_orders/{event_id}", headers=headers)
                    if r.status_code == 200:
                        d = r.json()
                        ext = d.get("external_reference") or ""
                        m = re.search(r"vendor-(\d+)-", ext)
                        if m:
                            vendor_id = int(m.group(1))
                        if "lifetime" in ext:
                            mode_meta = "lifetime"
                        else:
                            payments = d.get("payments") or []
                            if payments:
                                pid = payments[0].get("id")
                                if pid:
                                    rp = await client.get(f"https://api.mercadopago.com/v1/payments/{pid}", headers=headers)
                                    if rp.status_code == 200:
                                        pd = rp.json()
                                        vendor_id = pd.get("metadata", {}).get("vendor_id")
                                        mode_meta = mode_meta or pd.get("metadata", {}).get("mode")
                                        if vendor_id is None:
                                            ext2 = pd.get("external_reference") or ""
                                            m2 = re.search(r"vendor-(\d+)-", ext2)
                                            if m2:
                                                vendor_id = int(m2.group(1))
                                            if "lifetime" in ext2:
                                                mode_meta = "lifetime"
        except httpx.HTTPError:
            pass

    if vendor_id is None:
        return {"status": "ok"}

    if topic in ("payment", "subscription_paid", "payment.updated", "merchant_order"):
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if mode_meta == "lifetime":
            state = await billing_repo.get_access_state(session, int(vendor_id))
            if settings.MP_ACCESS_TOKEN and getattr(state, "subscription_id_mp", None):
                url = f"https://api.mercadopago.com/preapproval/{state.subscription_id_mp}"
                headers = {
                    "Authorization": f"Bearer {settings.MP_ACCESS_TOKEN}",
                    "Content-Type": "application/json",
                }
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        await client.put(url, headers=headers, json={"status": "cancelled"})
                except httpx.HTTPError:
                    pass
            updates = {"_action": "set_lifetime", "access_mode": "lifetime", "source": "lifetime_purchase", "valid_until": None, "subscription_id_mp": None}
            await billing_repo.upsert_access_state(session, int(vendor_id), updates)
            await billing_repo.save_billing_event(session, vendor_id=int(vendor_id), event_type="lifetime_activated", mp_event_id=mp_event_id, raw_payload=payload, normalized=updates)
        else:
            updates = {"_action": "extend_subscription"}
            updates["access_mode"] = "subscription"
            updates["source"] = "paid_subscription"
            updates["valid_until"] = now + timedelta(days=30)
            await billing_repo.upsert_access_state(session, int(vendor_id), updates)
            await billing_repo.save_billing_event(session, vendor_id=int(vendor_id), event_type="subscription_renewed", mp_event_id=mp_event_id, raw_payload=payload, normalized=updates)
    elif topic in ("payment_failed", "subscription_past_due"):
        updates = {"_action": "mark_past_due"}
        await billing_repo.save_billing_event(session, vendor_id=int(vendor_id), event_type="subscription_past_due", mp_event_id=mp_event_id, raw_payload=payload, normalized=updates)
    else:
        await billing_repo.save_billing_event(session, vendor_id=int(vendor_id), event_type=topic, mp_event_id=mp_event_id, raw_payload=payload, normalized=None)

    return {"status": "ok"}

@router.get("/webhooks/mp/health", status_code=status.HTTP_200_OK)
async def webhook_health():
    return {"status": "ok"}

@router.get("/return")
async def mp_return(request: Request):
    qs = request.url.query
    target = f"http://localhost:3000/settings/billing"
    if qs:
        target = f"{target}?{qs}"
    return RedirectResponse(url=target, status_code=status.HTTP_302_FOUND)

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
    return res
