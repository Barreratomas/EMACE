from typing import Any, Dict, Optional
from uuid import uuid4
import logging
import time
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from langchain_core.messages import HumanMessage, AIMessage
import httpx
import re

from app.core.database.session import get_async_session
from app.core.database.models import User, Customer, VendorTelegramIntegration, AuditLog
from app.core.checkpoint import get_postgres_checkpointer
from app.graph.workflow import workflow as graph
from app.api.deps import get_current_user, get_tenant_owner_id
from app.core.config import settings
from app.core.security import encrypt_secret, decrypt_secret
from app.repositories.telegram_integration import telegram_integration_repo
from app.repositories.telegram_audit import telegram_integration_audit
from app.core.rate_limit import limiter, telegram_webhook_key
from app.repositories.mtproto_session import mtproto_session_repo
from app.core.telegram_mtproto import mtproto_manager
from app.core.botfather_orchestrator import botfather_orchestrator
from sqlalchemy import func

router = APIRouter()
logger = logging.getLogger(__name__)

MTPROTO_KILL_SWITCH_OVERRIDE: Optional[bool] = None
MTPROTO_ALLOWED_VENDORS_OVERRIDE: Optional[str] = None


def _is_mtproto_allowed(vendor_id: int) -> bool:
    if not settings.TELEGRAM_MTPROTO_ENABLED:
        return False
    if MTPROTO_KILL_SWITCH_OVERRIDE is not None:
        if MTPROTO_KILL_SWITCH_OVERRIDE:
            return False
    elif settings.TELEGRAM_MTPROTO_KILL_SWITCH:
        return False
    allowed = MTPROTO_ALLOWED_VENDORS_OVERRIDE if MTPROTO_ALLOWED_VENDORS_OVERRIDE is not None else settings.TELEGRAM_MTPROTO_ALLOWED_VENDORS
    if not allowed:
        return True
    items = [x.strip() for x in allowed.split(",") if x.strip()]
    return str(vendor_id) in items


async def _get_vendor_by_public_id(session: AsyncSession, vendor_public_id: str) -> Optional[User]:
    if vendor_public_id.isdigit():
        result = await session.execute(select(User).where(User.id == int(vendor_public_id)))
        return result.scalar_one_or_none()
    result = await session.execute(select(User).where(User.email == vendor_public_id))
    found = result.scalar_one_or_none()
    if found:
        return found
    result = await session.execute(select(User).where(User.name == vendor_public_id))
    return result.scalar_one_or_none()


def _extract_message(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    msg = payload.get("message")
    if not msg:
        return None
    chat = msg.get("chat") or {}
    text = msg.get("text")
    if not (chat and text):
        return None
    return {"chat_id": str(chat.get("id")), "text": text}


def ensure_bot_management_permissions(user: User) -> None:
    if user.role and user.role.name == "admin":
        return
    if user.parent_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="bot_management_forbidden",
        )


@router.post("/telegram/webhook/{vendor_public_id}/{webhook_secret}")
@limiter.limit("60/minute", key_func=telegram_webhook_key)
async def telegram_webhook(
    vendor_public_id: str,
    webhook_secret: str,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="invalid_payload")

    print("telegram_webhook: payload_received", {"vendor_public_id": vendor_public_id, "has_payload": bool(payload)})

    vendor = await _get_vendor_by_public_id(session, vendor_public_id)
    if not vendor:
        print("telegram_webhook: vendor_not_found", {"vendor_public_id": vendor_public_id})
        raise HTTPException(status_code=404, detail="vendor_not_found")

    result = await session.execute(
        select(VendorTelegramIntegration).where(VendorTelegramIntegration.vendor_id == vendor.id)
    )
    integration = result.scalar_one_or_none()
    if (
        not integration
        or not integration.is_active
        or integration.state == "deleted"
        or integration.webhook_secret != webhook_secret
    ):
        print(
            "telegram_webhook: unauthorized_integration",
            {
                "vendor_id": vendor.id,
                "has_integration": bool(integration),
                "is_active": getattr(integration, "is_active", None),
                "state": getattr(integration, "state", None),
                "webhook_secret_matches": getattr(integration, "webhook_secret", None) == webhook_secret if integration else None,
            },
        )
        raise HTTPException(status_code=403, detail="unauthorized_webhook")

    message = _extract_message(payload)
    if not message:
        print("telegram_webhook: no_message_extracted", {"payload_keys": list(payload.keys())})
        return {"ok": True}

    chat_id = message["chat_id"]
    text = message["text"]

    print(
        "telegram_webhook: message_extracted",
        {"vendor_id": vendor.id, "chat_id": chat_id, "text_preview": text[:80]},
    )

    cust_res = await session.execute(select(Customer).where(Customer.telegram_chat_id == chat_id))
    customer = cust_res.scalar_one_or_none()
    customer_id = customer.id if customer else None

    logger.info(
        {
            "event": "telegram.webhook.received",
            "vendor_id": vendor.id,
            "chat_id": chat_id,
        }
    )

    start = time.monotonic()
    success = False

    reply_text: Optional[str] = None
    async with get_postgres_checkpointer() as checkpointer:
        app = graph.compile(checkpointer=checkpointer)
        config = {
            "configurable": {
                "thread_id": f"telegram_{chat_id}",
                "user_id": vendor.id,
                "customer_id": customer_id,
                "channel": "telegram_vendor_bot",
                "user_role": "customer",
                "user_permissions": ["customer:access"],
            }
        }
        try:
            print("telegram_webhook: invoking_graph", {"vendor_id": vendor.id, "chat_id": chat_id})
            result = await app.ainvoke({"messages": [HumanMessage(content=text)]}, config)
            try:
                msgs = result.get("messages", []) if isinstance(result, dict) else []
                for m in reversed(msgs):
                    if isinstance(m, AIMessage) and m.content:
                        if "QA Notification" not in str(m.content):
                            reply_text = str(m.content)
                            break
            except Exception:
                reply_text = None
            success = True
            print(
                "telegram_webhook: graph_completed",
                {"vendor_id": vendor.id, "chat_id": chat_id, "has_reply": bool(reply_text)},
            )
        except Exception as e:
            logger.exception(
                {
                    "event": "telegram.webhook.error",
                    "vendor_id": vendor.id,
                    "chat_id": chat_id,
                }
            )
            print(
                "telegram_webhook: graph_error",
                {"vendor_id": vendor.id, "chat_id": chat_id, "error": str(e)[:200]},
            )
            integration.last_error = str(e)[:500]
            await session.commit()

    duration_ms = int((time.monotonic() - start) * 1000)
    logger.info(
        {
            "event": "telegram.webhook.processed",
            "vendor_id": vendor.id,
            "chat_id": chat_id,
            "success": success,
            "duration_ms": duration_ms,
        }
    )

    metric = AuditLog(
        user_id=vendor.id,
        agent_name="TelegramWebhook",
        action="telegram_webhook_metric",
        details=f"vendor_id={vendor.id}|chat_id={chat_id}|success={success}|duration_ms={duration_ms}",
        timestamp=datetime.now(timezone.utc),
    )
    session.add(metric)
    await session.commit()

    # Responder al cliente de Telegram usando el bot del vendor (si hay respuesta)
    if reply_text:
        try:
            token = decrypt_secret(integration.bot_token_encrypted)
        except Exception:
            token = None
        if token:
            try:
                print(
                    "telegram_webhook: sending_reply",
                    {"vendor_id": vendor.id, "chat_id": chat_id, "reply_preview": reply_text[:80]},
                )
                async with httpx.AsyncClient(timeout=10) as client:
                    await client.post(
                        f"https://api.telegram.org/bot{token}/sendMessage",
                        json={"chat_id": chat_id, "text": reply_text},
                    )
            except httpx.HTTPError:
                pass

    return {"ok": True}


@router.get("/telegram/admin/mtproto/state", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def mtproto_admin_state(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    if not current_user.role or current_user.role.name != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin_required")
    return {
        "enabled": settings.TELEGRAM_MTPROTO_ENABLED,
        "kill_switch": MTPROTO_KILL_SWITCH_OVERRIDE if MTPROTO_KILL_SWITCH_OVERRIDE is not None else settings.TELEGRAM_MTPROTO_KILL_SWITCH,
        "allowed_vendors": MTPROTO_ALLOWED_VENDORS_OVERRIDE if MTPROTO_ALLOWED_VENDORS_OVERRIDE is not None else (settings.TELEGRAM_MTPROTO_ALLOWED_VENDORS or ""),
        "override_active": {
            "kill_switch": MTPROTO_KILL_SWITCH_OVERRIDE is not None,
            "allowed_vendors": MTPROTO_ALLOWED_VENDORS_OVERRIDE is not None,
        },
    }


@router.post("/telegram/admin/mtproto/kill-switch", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def mtproto_admin_kill_switch(
    request: Request,
    body: Dict[str, Any],
    current_user: User = Depends(get_current_user),
):
    if not current_user.role or current_user.role.name != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin_required")
    value = body.get("value")
    if value is None:
        raise HTTPException(status_code=400, detail="value_required")
    global MTPROTO_KILL_SWITCH_OVERRIDE
    MTPROTO_KILL_SWITCH_OVERRIDE = bool(value)
    return {"ok": True, "kill_switch": MTPROTO_KILL_SWITCH_OVERRIDE}


@router.post("/telegram/admin/mtproto/allowlist", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def mtproto_admin_allowlist_set(
    request: Request,
    body: Dict[str, Any],
    current_user: User = Depends(get_current_user),
):
    if not current_user.role or current_user.role.name != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin_required")
    val = body.get("vendors")
    if val is None:
        raise HTTPException(status_code=400, detail="vendors_required")
    global MTPROTO_ALLOWED_VENDORS_OVERRIDE
    s = str(val).strip()
    MTPROTO_ALLOWED_VENDORS_OVERRIDE = s
    return {"ok": True, "allowed_vendors": MTPROTO_ALLOWED_VENDORS_OVERRIDE}


@router.post("/telegram/admin/mtproto/allowlist/add", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def mtproto_admin_allowlist_add(
    request: Request,
    body: Dict[str, Any],
    current_user: User = Depends(get_current_user),
):
    if not current_user.role or current_user.role.name != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin_required")
    vendor = body.get("vendor_id")
    if vendor is None:
        raise HTTPException(status_code=400, detail="vendor_id_required")
    global MTPROTO_ALLOWED_VENDORS_OVERRIDE
    base = MTPROTO_ALLOWED_VENDORS_OVERRIDE if MTPROTO_ALLOWED_VENDORS_OVERRIDE is not None else (settings.TELEGRAM_MTPROTO_ALLOWED_VENDORS or "")
    items = [x.strip() for x in base.split(",") if x.strip()]
    if str(vendor) not in items:
        items.append(str(vendor))
    MTPROTO_ALLOWED_VENDORS_OVERRIDE = ",".join(items) if items else ""
    return {"ok": True, "allowed_vendors": MTPROTO_ALLOWED_VENDORS_OVERRIDE}


@router.post("/telegram/admin/mtproto/allowlist/remove", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def mtproto_admin_allowlist_remove(
    request: Request,
    body: Dict[str, Any],
    current_user: User = Depends(get_current_user),
):
    if not current_user.role or current_user.role.name != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin_required")
    vendor = body.get("vendor_id")
    if vendor is None:
        raise HTTPException(status_code=400, detail="vendor_id_required")
    global MTPROTO_ALLOWED_VENDORS_OVERRIDE
    base = MTPROTO_ALLOWED_VENDORS_OVERRIDE if MTPROTO_ALLOWED_VENDORS_OVERRIDE is not None else (settings.TELEGRAM_MTPROTO_ALLOWED_VENDORS or "")
    items = [x.strip() for x in base.split(",") if x.strip()]
    items = [x for x in items if x != str(vendor)]
    MTPROTO_ALLOWED_VENDORS_OVERRIDE = ",".join(items) if items else ""
    return {"ok": True, "allowed_vendors": MTPROTO_ALLOWED_VENDORS_OVERRIDE}


@router.get("/telegram/admin/integrations", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def list_telegram_integrations(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    if not current_user.role or current_user.role.name != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin_required")

    result = await session.execute(select(VendorTelegramIntegration))
    integrations = result.scalars().all()
    items = []
    for integration in integrations:
        metrics_result = await session.execute(
            select(AuditLog)
            .where(
                AuditLog.user_id == integration.vendor_id,
                AuditLog.action == "telegram_webhook_metric",
            )
            .order_by(AuditLog.timestamp.desc())
            .limit(1)
        )
        last_metric = metrics_result.scalars().first()
        last_latency_ms: Optional[int] = None
        if last_metric:
            for part in last_metric.details.split("|"):
                if part.startswith("duration_ms="):
                    try:
                        last_latency_ms = int(part.split("=", 1)[1])
                    except ValueError:
                        last_latency_ms = None
                    break

        integration_status = "inactive"
        if integration.is_active:
            integration_status = "degraded" if integration.last_error else "healthy"

        items.append(
            {
                "vendor_id": integration.vendor_id,
                "bot_username": integration.bot_username,
                "is_active": integration.is_active,
                "status": integration_status,
                "last_error": integration.last_error,
                "last_latency_ms": last_latency_ms,
                "last_metric_at": last_metric.timestamp.isoformat() if last_metric else None,
                "created_at": integration.created_at.isoformat() if integration.created_at else None,
                "updated_at": integration.updated_at.isoformat() if integration.updated_at else None,
            }
        )
    logger.info(
        {
            "event": "telegram.admin.integrations.list",
            "admin_id": current_user.id,
            "count": len(items),
        }
    )
    return {"items": items}


@router.post("/telegram/admin/integrations/{vendor_id}/suspend", status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def suspend_telegram_integration(
    vendor_id: int,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    if not current_user.role or current_user.role.name != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin_required")

    result = await session.execute(
        select(VendorTelegramIntegration).where(VendorTelegramIntegration.vendor_id == vendor_id)
    )
    integration = result.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=404, detail="integration_not_found")

    token = None
    try:
        token = decrypt_secret(integration.bot_token_encrypted)
    except Exception:
        token = None

    integration.is_active = False
    await session.commit()

    if token:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(f"https://api.telegram.org/bot{token}/setWebhook", json={"url": ""})
        except httpx.HTTPError:
            pass

    await telegram_integration_audit.log_integration_change(
        session=session,
        vendor_id=vendor_id,
        actor_user_id=current_user.id,
        action="telegram_bot_suspended",
        old_state={"active": True},
        new_state={"active": False},
    )
    logger.info(
        {
            "event": "telegram.admin.integration.suspended",
            "admin_id": current_user.id,
            "vendor_id": vendor_id,
        }
    )
    return {"ok": True}

@router.post("/vendors/me/integrations/telegram/bot/pause", status_code=status.HTTP_200_OK)
async def pause_vendor_bot(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    ensure_bot_management_permissions(current_user)
    vendor_id = get_tenant_owner_id(current_user)
    result = await session.execute(
        select(VendorTelegramIntegration).where(VendorTelegramIntegration.vendor_id == vendor_id)
    )
    integration = result.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=404, detail="integration_not_found")
    if integration.state == "deleted":
        raise HTTPException(status_code=400, detail="integration_deleted")
    if integration.state == "paused":
        return {"ok": True}
    token = None
    try:
        token = decrypt_secret(integration.bot_token_encrypted)
    except Exception:
        token = None
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    integration.is_active = False
    integration.state = "paused"
    integration.paused_at = now
    integration.paused_by_user_id = current_user.id
    integration.updated_at = now
    await session.commit()
    if token:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(f"https://api.telegram.org/bot{token}/setWebhook", json={"url": ""})
        except httpx.HTTPError:
            pass
    await telegram_integration_audit.log_integration_change(
        session=session,
        vendor_id=vendor_id,
        actor_user_id=current_user.id,
        action="bot_paused",
        old_state={"active": True},
        new_state={"active": False, "state": "paused"},
    )
    return {"ok": True}

@router.post("/vendors/me/integrations/telegram/bot/resume", status_code=status.HTTP_200_OK)
async def resume_vendor_bot(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    ensure_bot_management_permissions(current_user)
    vendor_id = get_tenant_owner_id(current_user)
    result = await session.execute(
        select(VendorTelegramIntegration).where(VendorTelegramIntegration.vendor_id == vendor_id)
    )
    integration = result.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=404, detail="integration_not_found")
    if integration.state == "deleted":
        raise HTTPException(status_code=400, detail="integration_deleted")
    if integration.state == "active" and integration.is_active:
        return {"ok": True}
    try:
        token = decrypt_secret(integration.bot_token_encrypted)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid_encrypted_token")
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    base = str(request.base_url).rstrip("/")
    webhook_url = f"{base}{settings.API_V1_STR}/telegram/webhook/{vendor_id}/{integration.webhook_secret}"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(f"https://api.telegram.org/bot{token}/setWebhook", json={"url": webhook_url})
    except httpx.HTTPError:
        raise HTTPException(status_code=400, detail="telegram_api_unreachable")
    integration.is_active = True
    integration.state = "active"
    integration.paused_at = None
    integration.paused_by_user_id = None
    integration.updated_at = now
    await session.commit()
    await telegram_integration_audit.log_integration_change(
        session=session,
        vendor_id=vendor_id,
        actor_user_id=current_user.id,
        action="bot_resumed",
        old_state={"active": False},
        new_state={"active": True, "state": "active"},
    )
    return {"ok": True}

@router.patch("/vendors/me/integrations/telegram/bot", status_code=status.HTTP_200_OK)
async def update_vendor_bot_properties(
    request: Request,
    body: Dict[str, Any] | None = None,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    ensure_bot_management_permissions(current_user)
    vendor_id = get_tenant_owner_id(current_user)
    result = await session.execute(
        select(VendorTelegramIntegration).where(VendorTelegramIntegration.vendor_id == vendor_id)
    )
    integration = result.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=404, detail="integration_not_found")
    body = body or {}
    regenerate_ws = bool(body.get("regenerate_webhook_secret"))
    updated_fields: Dict[str, Any] = {}
    if regenerate_ws:
        integration.webhook_secret = uuid4().hex
        updated_fields["webhook_secret"] = True
        if integration.is_active and integration.state == "active":
            try:
                token = decrypt_secret(integration.bot_token_encrypted)
            except Exception:
                raise HTTPException(status_code=400, detail="invalid_encrypted_token")
            base = str(request.base_url).rstrip("/")
            webhook_url = f"{base}{settings.API_V1_STR}/telegram/webhook/{vendor_id}/{integration.webhook_secret}"
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    await client.post(f"https://api.telegram.org/bot{token}/setWebhook", json={"url": webhook_url})
            except httpx.HTTPError:
                raise HTTPException(status_code=400, detail="telegram_api_unreachable")
    if not updated_fields:
        return {"ok": True, "updated": []}
    integration.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await session.commit()
    await telegram_integration_audit.log_integration_change(
        session=session,
        vendor_id=vendor_id,
        actor_user_id=current_user.id,
        action="bot_properties_updated",
        old_state={},
        new_state=updated_fields,
    )
    return {"ok": True, "updated": list(updated_fields.keys())}

@router.delete("/vendors/me/integrations/telegram/bot", status_code=status.HTTP_200_OK)
async def delete_vendor_bot(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    ensure_bot_management_permissions(current_user)
    vendor_id = get_tenant_owner_id(current_user)
    result = await session.execute(
        select(VendorTelegramIntegration).where(VendorTelegramIntegration.vendor_id == vendor_id)
    )
    integration = result.scalar_one_or_none()
    if not integration:
        raise HTTPException(status_code=404, detail="integration_not_found")
    if integration.state == "deleted":
        return {"ok": True}
    token = None
    try:
        token = decrypt_secret(integration.bot_token_encrypted)
    except Exception:
        token = None
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    integration.is_active = False
    integration.state = "deleted"
    integration.deleted_at = now
    integration.updated_at = now
    await session.commit()
    if token:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(f"https://api.telegram.org/bot{token}/setWebhook", json={"url": ""})
        except httpx.HTTPError:
            pass
    await telegram_integration_audit.log_integration_change(
        session=session,
        vendor_id=vendor_id,
        actor_user_id=current_user.id,
        action="bot_deleted",
        old_state={"active": True},
        new_state={"active": False, "state": "deleted"},
    )
    return {"ok": True}
@router.get("/vendors/me/integrations/telegram/status", status_code=status.HTTP_200_OK)
async def get_vendor_telegram_status(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    vendor_id = get_tenant_owner_id(current_user)
    result = await session.execute(
        select(VendorTelegramIntegration).where(VendorTelegramIntegration.vendor_id == vendor_id)
    )
    integration = result.scalar_one_or_none()
    if not integration:
        return {"has_integration": False}
    metrics_result = await session.execute(
        select(AuditLog)
        .where(
            AuditLog.user_id == vendor_id,
            AuditLog.action == "telegram_webhook_metric",
        )
        .order_by(AuditLog.timestamp.desc())
        .limit(1)
    )
    last_metric = metrics_result.scalars().first()
    last_latency_ms: Optional[int] = None
    last_metric_at: Optional[str] = None
    if last_metric:
        last_metric_at = last_metric.timestamp.isoformat()
        for part in last_metric.details.split("|"):
            if part.startswith("duration_ms="):
                try:
                    last_latency_ms = int(part.split("=", 1)[1])
                except ValueError:
                    last_latency_ms = None
                break
    status_str = "inactive"
    if integration.is_active:
        status_str = "degraded" if integration.last_error else "healthy"
    base = str(request.base_url).rstrip("/")
    webhook_url = f"{base}{settings.API_V1_STR}/telegram/webhook/{vendor_id}/{integration.webhook_secret}"
    return {
        "has_integration": True,
        "vendor_id": integration.vendor_id,
        "bot_username": integration.bot_username,
        "webhook_url": webhook_url,
        "is_active": integration.is_active,
        "state": getattr(integration, "state", None),
        "status": status_str,
        "last_error": integration.last_error,
        "last_latency_ms": last_latency_ms,
        "last_metric_at": last_metric_at,
    }


@router.post("/vendors/me/integrations/telegram/mtproto/consent", status_code=status.HTTP_200_OK)
async def accept_mtproto_consent(
    request: Request,
    body: Dict[str, Any],
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    vendor_id = get_tenant_owner_id(current_user)
    ip = request.client.host if request.client else None
    print(
        {
            "event": "mtproto.consent.request",
            "vendor_id": vendor_id,
            "ip": ip,
        }
    )
    allowed = _is_mtproto_allowed(vendor_id)
    if not allowed:
        print(
            {
                "event": "mtproto.consent.blocked",
                "vendor_id": vendor_id,
                "ip": ip,
            }
        )
        raise HTTPException(status_code=503, detail="mtproto_unavailable")
    accepted = body.get("accepted")
    terms_version = body.get("terms_version") or "v1"
    if not accepted:
        raise HTTPException(status_code=400, detail="consent_not_accepted")
    details = f"vendor_id={vendor_id}|terms_version={terms_version}"
    if ip:
        details = f"{details}|ip={ip}"
    log = AuditLog(
        user_id=vendor_id,
        agent_name="TelegramMtproto",
        action="telegram_mtproto_consent",
        details=details,
        timestamp=datetime.now(timezone.utc),
    )
    session.add(log)
    await session.commit()
    logger.info(
        {
            "event": "mtproto.consent.accepted",
            "vendor_id": vendor_id,
            "ip": ip,
            "terms_version": terms_version,
        }
    )
    return {"ok": True, "terms_version": terms_version}

# -------------------------
# Modo C (MTProto) - Endpoints de scaffolding
# -------------------------

@router.get("/vendors/me/integrations/telegram/mtproto/status", status_code=status.HTTP_200_OK)
async def get_mtproto_status(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    vendor_id = get_tenant_owner_id(current_user)
    allowed = _is_mtproto_allowed(vendor_id)
    record = await mtproto_session_repo.get_by_vendor_id(session, vendor_id)
    return {
        "vendor_id": vendor_id,
        "allowed": allowed,
        "mtproto_enabled": bool(record.enabled) if record else False,
        "mtproto_status": record.status if record else "inactive",
        "last_heartbeat_at": record.last_heartbeat_at.isoformat() if record and record.last_heartbeat_at else None,
        "last_error": record.last_error if record else None,
    }

@router.post("/vendors/me/integrations/telegram/bot/auto-create", status_code=status.HTTP_202_ACCEPTED)
async def bot_auto_create(
    body: Dict[str, Any],
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    vendor_id = get_tenant_owner_id(current_user)
    allowed = _is_mtproto_allowed(vendor_id)
    if not allowed:
        raise HTTPException(status_code=503, detail="mtproto_unavailable")
    record = await mtproto_session_repo.get_by_vendor_id(session, vendor_id)
    if not record or not record.enabled or record.status not in ("ready", "enabled"):
        raise HTTPException(status_code=400, detail="session_not_configured")
    bot_name = str(body.get("bot_name") or "").strip()
    username_hint = str(body.get("username_hint") or "").strip()
    if not bot_name or not username_hint:
        raise HTTPException(status_code=400, detail="bot_name_and_username_required")
    # Límite: solo 1 bot por vendor hasta que se elimine la integración
    existing = await telegram_integration_repo.get_by_vendor_id(session, vendor_id)
    if existing and existing.state != "deleted":
        raise HTTPException(status_code=409, detail="bot_already_exists")
    if botfather_orchestrator.has_active(vendor_id):
        raise HTTPException(status_code=409, detail="creation_in_progress")
    await botfather_orchestrator.start_auto_create(vendor_id, bot_name, username_hint)
    log = AuditLog(
        user_id=vendor_id,
        agent_name="BotFatherOrchestrator",
        action="bot_auto_create_requested",
        details=f"name={bot_name}|username_hint={username_hint}",
        timestamp=datetime.now(timezone.utc),
    )
    session.add(log)
    await session.commit()
    return {"ok": True, "status": "creating"}

@router.get("/vendors/me/integrations/telegram/bot/status", status_code=status.HTTP_200_OK)
async def bot_auto_create_status(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    vendor_id = get_tenant_owner_id(current_user)
    state = botfather_orchestrator.get_state(vendor_id)
    result = await session.execute(
        select(VendorTelegramIntegration).where(VendorTelegramIntegration.vendor_id == vendor_id)
    )
    integration = result.scalar_one_or_none()
    status_str = "none"
    last_error = None
    started_at = None
    if state:
        started_at = state.started_at
        last_error = state.last_error
        if state.status in ("sent_newbot", "sent_name", "sent_username", "waiting_token"):
            status_str = "creating"
        elif state.status == "completed":
            status_str = "ready"
        elif state.status == "failed":
            status_str = "error"
    elif integration and integration.is_active:
        status_str = "ready"
    return {
        "bot_status": status_str,
        "bot_username": integration.bot_username if integration else None,
        "last_error": last_error or (integration.last_error if integration else None),
        "started_at": started_at,
    }


@router.post("/vendors/me/integrations/telegram/mtproto/session/init", status_code=status.HTTP_202_ACCEPTED)
async def init_mtproto_session(
    request: Request,
    body: Dict[str, Any] | None = None,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    vendor_id = get_tenant_owner_id(current_user)
    ip = request.client.host if request.client else None
    print(
        {
            "event": "mtproto.session.init.request",
            "vendor_id": vendor_id,
            "ip": ip,
        }
    )
    if not _is_mtproto_allowed(vendor_id):
        print(
            {
                "event": "mtproto.session.init.blocked",
                "vendor_id": vendor_id,
                "ip": ip,
            }
        )
        raise HTTPException(status_code=503, detail="mtproto_unavailable")
    phone_number = (body or {}).get("phone_number")
    if phone_number:
        pn = str(phone_number).strip()
        pn = re.sub(r"[()\s\-]", "", pn)
        if pn.startswith("00"):
            pn = f"+{pn[2:]}"
        if not pn.startswith("+"):
            print(
                {
                    "event": "mtproto.session.init.invalid_phone",
                    "vendor_id": vendor_id,
                    "ip": ip,
                    "reason": "missing_plus",
                }
            )
            raise HTTPException(status_code=400, detail="invalid_phone_number")
        if not re.match(r"^\+[1-9]\d{7,14}$", pn):
            print(
                {
                    "event": "mtproto.session.init.invalid_phone",
                    "vendor_id": vendor_id,
                    "ip": ip,
                    "reason": "format_e164",
                }
            )
            raise HTTPException(status_code=400, detail="invalid_phone_number")
        try:
            pending_session = await mtproto_manager.create_pending_session(pn)
        except Exception as e:
            print(
                {
                    "event": "mtproto.session.init.error",
                    "vendor_id": vendor_id,
                    "ip": ip,
                    "error": str(e)[:200],
                }
            )
            raise HTTPException(status_code=400, detail="mtproto_login_error") from e
        enc = encrypt_secret(pending_session)
        await mtproto_session_repo.upsert(
            session=session,
            vendor_id=vendor_id,
            phone_number=pn,
            session_encrypted=enc,
            status="awaiting_code",
            enabled=False,
            last_error=None,
        )
        print(
            {
                "event": "mtproto.session.init.phone_set",
                "vendor_id": vendor_id,
                "ip": ip,
            }
        )
    else:
        await mtproto_session_repo.upsert(
            session=session,
            vendor_id=vendor_id,
            status="pending_login",
            enabled=False,
            last_error=None,
        )
        print(
            {
                "event": "mtproto.session.init.pending_login",
                "vendor_id": vendor_id,
                "ip": ip,
            }
        )
    challenge_id = uuid4().hex
    print(
        {"event": "mtproto.session.init.requested", "vendor_id": vendor_id, "challenge_id": challenge_id}
    )
    # Se registra auditoría mínima
    log = AuditLog(
        user_id=vendor_id,
        agent_name="TelegramMtproto",
        action="mtproto_session_init_requested",
        details=f"challenge_id={challenge_id}",
        timestamp=datetime.now(timezone.utc),
    )
    session.add(log)
    await session.commit()
    return {
        "challenge_id": challenge_id,
        "mode": "code_or_qr",
        "expires_in_seconds": 300,
        "message": "Login MTProto solicitado, pendiente de confirmación",
    }


@router.post("/vendors/me/integrations/telegram/mtproto/session/confirm", status_code=status.HTTP_202_ACCEPTED)
async def confirm_mtproto_session(
    body: Dict[str, Any],
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    vendor_id = get_tenant_owner_id(current_user)
    ip = "unknown"
    code_len = len(body.get("code", "")) if isinstance(body.get("code", ""), str) else None
    provided_kind = "session_string" if body.get("session_string") else ("code" if body.get("code") else ("qr_token" if body.get("qr_token") else None))
    logger.info(
        "LOG en confirm_mtproto_session: mtproto.session.confirm.request",
        {
            "event": "mtproto.session.confirm.request",
            "vendor_id": vendor_id,
            "ip": ip,
            "provided": provided_kind,
            "code_len": code_len,
        }
    )
    if not _is_mtproto_allowed(vendor_id):
        logger.warning(
            "LOG en confirm_mtproto_session: mtproto.session.confirm.blocked",
            {
                "event": "mtproto.session.confirm.blocked",
                "vendor_id": vendor_id,
                "ip": ip,
            }
        )
        raise HTTPException(status_code=503, detail="mtproto_unavailable")
    code = body.get("code")
    qr_token = body.get("qr_token")
    session_string = body.get("session_string")
    if not code and not qr_token and not session_string:
        logger.warning(
            "LOG en confirm_mtproto_session: mtproto.session.confirm.invalid_payload",
            {
                "event": "mtproto.session.confirm.invalid_payload",
                "vendor_id": vendor_id,
                "ip": ip,
            }
        )
        raise HTTPException(status_code=400, detail="code_or_qr_or_session_required")
    status_value = "awaiting_session"
    if session_string:
        enc = encrypt_secret(session_string)
        await mtproto_session_repo.upsert(
            session=session,
            vendor_id=vendor_id,
            session_encrypted=enc,
            status="ready",
            enabled=False,
            last_error=None,
        )
        logger.info(
            "LOG en confirm_mtproto_session: mtproto.session.confirm.session_set",
            {
                "event": "mtproto.session.confirm.session_set",
                "vendor_id": vendor_id,
                "ip": ip,
                "status": "ready",
            }
        )
        status_value = "ready"
    elif code:
        record = await mtproto_session_repo.get_by_vendor_id(session, vendor_id)
        if not record or not record.session_encrypted:
            logger.warning(
                "LOG en confirm_mtproto_session: mtproto.session.confirm.pending_required",
                {
                    "event": "mtproto.session.confirm.pending_required",
                    "vendor_id": vendor_id,
                    "ip": ip,
                }
            )
            raise HTTPException(status_code=400, detail="pending_session_required")
        phone_number = record.phone_number or body.get("phone_number")
        if not phone_number:
            logger.warning(
                "LOG en confirm_mtproto_session: mtproto.session.confirm.phone_required",
                {
                    "event": "mtproto.session.confirm.phone_required",
                    "vendor_id": vendor_id,
                    "ip": ip,
                }
            )
            raise HTTPException(status_code=400, detail="phone_required")
        try:
            pending = decrypt_secret(record.session_encrypted)
            logger.info(
                "LOG en confirm_mtproto_session: mtproto.session.confirm.finalize.attempt",
                {
                    "event": "mtproto.session.confirm.finalize.attempt",
                    "vendor_id": vendor_id,
                    "ip": ip,
                }
            )
            final_session = await mtproto_manager.finalize_session(pending, phone_number, code)
        except Exception as e:
            logger.error(
                f"LOG en confirm_mtproto_session: mtproto.session.confirm.error "
                f"vendor_id={vendor_id} ip={ip} error={str(e)[:200]}"
            )
            raise HTTPException(status_code=400, detail="mtproto_login_error") from e
        enc = encrypt_secret(final_session)
        await mtproto_session_repo.upsert(
            session=session,
            vendor_id=vendor_id,
            session_encrypted=enc,
            status="ready",
            enabled=False,
            last_error=None,
        )
        logger.info(
            "LOG en confirm_mtproto_session: mtproto.session.confirm.ready",
            {
                "event": "mtproto.session.confirm.ready",
                "vendor_id": vendor_id,
                "ip": ip,
                "status": "ready",
            }
        )
        status_value = "ready"
    else:
        await mtproto_session_repo.upsert(
            session=session,
            vendor_id=vendor_id,
            status="awaiting_session",
            enabled=False,
        )
        logger.info(
            "LOG en confirm_mtproto_session: mtproto.session.confirm.qr_pending",
            {
                "event": "mtproto.session.confirm.qr_pending",
                "vendor_id": vendor_id,
                "ip": ip,
                "status": "awaiting_session",
            }
        )
    logger.info(
        "LOG en confirm_mtproto_session: mtproto.session.confirm.requested",
        {
            "event": "mtproto.session.confirm.requested",
            "vendor_id": vendor_id,
            "provided": "session_string" if session_string else ("code" if code else "qr_token"),
        }
    )
    log = AuditLog(
        user_id=vendor_id,
        agent_name="TelegramMtproto",
        action="mtproto_session_confirm_requested",
        details=f"provided={'session_string' if session_string else ('code' if code else 'qr')}",
        timestamp=datetime.now(timezone.utc),
    )
    session.add(log)
    await session.commit()
    return {"ok": True, "status": status_value}


@router.post("/vendors/me/integrations/telegram/mtproto/enable", status_code=status.HTTP_202_ACCEPTED)
async def enable_mtproto(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    vendor_id = get_tenant_owner_id(current_user)
    logger.info(
        {
            "event": "mtproto.enable.request",
            "vendor_id": vendor_id,
        }
    )
    if not _is_mtproto_allowed(vendor_id):
        logger.warning(
            {
                "event": "mtproto.enable.blocked",
                "vendor_id": vendor_id,
            }
        )
        raise HTTPException(status_code=503, detail="mtproto_unavailable")
    rec = await mtproto_session_repo.get_by_vendor_id(session, vendor_id)
    if not rec or not rec.session_encrypted:
        raise HTTPException(status_code=400, detail="session_not_configured")
    await mtproto_session_repo.upsert(
        session=session, vendor_id=vendor_id, enabled=True, status="enabled", last_error=None
    )
    log = AuditLog(
        user_id=vendor_id,
        agent_name="TelegramMtproto",
        action="mtproto_enable_requested",
        details="",
        timestamp=datetime.now(timezone.utc),
    )
    session.add(log)
    await session.commit()
    logger.info(
        {
            "event": "mtproto.enable.accepted",
            "vendor_id": vendor_id,
        }
    )
    return {"ok": True, "mtproto_enabled": True, "status": "enabled"}


@router.post("/vendors/me/integrations/telegram/mtproto/disable", status_code=status.HTTP_200_OK)
async def disable_mtproto(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    vendor_id = get_tenant_owner_id(current_user)
    await mtproto_session_repo.upsert(
        session=session, vendor_id=vendor_id, enabled=False, status="inactive"
    )
    log = AuditLog(
        user_id=vendor_id,
        agent_name="TelegramMtproto",
        action="mtproto_disable_requested",
        details="",
        timestamp=datetime.now(timezone.utc),
    )
    session.add(log)
    await session.commit()
    return {"ok": True, "mtproto_enabled": False, "status": "inactive"}


@router.post("/vendors/me/integrations/telegram/mtproto/revoke", status_code=status.HTTP_200_OK)
async def revoke_mtproto_session(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    vendor_id = get_tenant_owner_id(current_user)
    record = await mtproto_session_repo.get_by_vendor_id(session, vendor_id)
    if not record or not record.session_encrypted:
        raise HTTPException(status_code=404, detail="session_not_found")
    await mtproto_session_repo.upsert(
        session=session,
        vendor_id=vendor_id,
        session_encrypted=None,
        enabled=False,
        status="inactive",
        last_error=None,
    )
    await mtproto_manager.disconnect_vendor(vendor_id)
    log = AuditLog(
        user_id=vendor_id,
        agent_name="TelegramMtproto",
        action="mtproto_session_revoked",
        details="",
        timestamp=datetime.now(timezone.utc),
    )
    session.add(log)
    await session.commit()
    return {"ok": True}
