import logging
import time
import httpx
from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Dict
from uuid import uuid4
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.models import User, VendorAccessState
from app.infrastructure.config import settings
from app.domain.ports.repositories import IBillingRepository

logger = logging.getLogger(__name__)

class BillingUseCases:
    def __init__(self, billing_repo: IBillingRepository):
        self.billing_repo = billing_repo

    def ensure_vendor(self, user: User):
        if user.parent_id is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Solo el Vendor puede gestionar billing"
            )

    async def create_mp_preference(self, vendor_id: int, body: Dict[str, Any]) -> str:
        if not settings.MP_ACCESS_TOKEN:
            return f"https://example.com/checkout/simulated?vendor={vendor_id}"

        base_url = "http://localhost:3000"
        if settings.MP_WEBHOOK_URL and "trycloudflare.com" in settings.MP_WEBHOOK_URL:
            parts = settings.MP_WEBHOOK_URL.split("/api/v1")
            if len(parts) > 0:
                base_url = parts[0]

        item = {
            "title": body.get("title", "Suscripción Mensual"),
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
        last_exc = None
        url = "https://api.mercadopago.com/checkout/preferences"
        
        for attempt in range(retries):
            try:
                t0 = time.perf_counter()
                async with httpx.AsyncClient(timeout=timeout) as client:
                    resp = await client.post(url, json=payload, headers=headers)
                
                if resp.status_code >= 200 and resp.status_code < 300:
                    data = resp.json()
                    return data.get("init_point") or data.get("sandbox_init_point") or ""
                
                if 500 <= resp.status_code < 600:
                    await time.sleep(0.5 * (2 ** attempt))
                    continue
                
                err_detail = resp.text
                try:
                    j = resp.json()
                    err_detail = j.get("message") or j.get("error") or j
                except: pass
                raise HTTPException(status_code=resp.status_code, detail=f"MP error: {err_detail}")
            except httpx.HTTPError as e:
                last_exc = e
                await time.sleep(0.5 * (2 ** attempt))
        
        raise HTTPException(status_code=502, detail=f"No se pudo crear preferencia en Mercado Pago: {last_exc}")

    async def get_access_state(self, session: AsyncSession, current_user: User):
        self.ensure_vendor(current_user)
        state = await self.billing_repo.get_access_state(session, current_user.id)
        if not state:
            await self.billing_repo.save_billing_event(
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

    async def create_subscription(self, session: AsyncSession, current_user: User, body: Dict[str, Any]) -> Dict[str, str]:
        self.ensure_vendor(current_user)
        
        state = await self.billing_repo.get_access_state(session, current_user.id)
        if state:
            if state.access_mode == "lifetime":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ya posees acceso de por vida. No es necesario suscribirse."
                )
            
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            if state.access_mode == "subscription" and state.valid_until and state.valid_until > now:
                if state.valid_until > now + timedelta(days=7):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Ya tienes una suscripción activa hasta el {state.valid_until.strftime('%d/%m/%Y')}. Podrás renovarla 7 días antes de su vencimiento."
                    )

        checkout_url = await self.create_mp_preference(current_user.id, body or {})

        await self.billing_repo.save_billing_event(
            session=session,
            vendor_id=current_user.id,
            event_type="subscription_create_requested",
            mp_event_id=None,
            raw_payload={"request": body},
            normalized={"checkout_url": checkout_url}
        )

        return {"checkout_url": checkout_url}

    async def cancel_subscription(self, session: AsyncSession, current_user: User, body: Dict[str, Any] | None = None) -> Dict[str, Any]:
        self.ensure_vendor(current_user)
        state = await self.billing_repo.get_access_state(session, current_user.id)
        if not state or state.access_mode != "subscription":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No hay suscripción activa para cancelar")
        
        if settings.MP_ACCESS_TOKEN and state.subscription_id_mp:
            url = f"https://api.mercadopago.com/preapproval/{state.subscription_id_mp}"
            headers = {
                "Authorization": f"Bearer {settings.MP_ACCESS_TOKEN}",
                "Content-Type": "application/json",
            }
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    await client.put(url, headers=headers, json={"status": "cancelled"})
            except: pass
            
        updates = {
            "subscription_id_mp": None,
            "_action": "cancel_subscription"
        }
        state = await self.billing_repo.upsert_access_state(session, current_user.id, updates, actor_user_id=current_user.id)
        await self.billing_repo.save_billing_event(
            session=session,
            vendor_id=current_user.id,
            event_type="subscription_cancel_requested",
            mp_event_id=None,
            raw_payload=body or {},
            normalized={"valid_until": state.valid_until}
        )
        return {"status": "ok", "valid_until": state.valid_until}
