import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from fastapi import HTTPException
from app.domain.models import User, Customer, VendorTelegramIntegration, AuditLog
from app.infrastructure.adapters.checkpoint import get_postgres_checkpointer
from app.application.graph.workflow import workflow as graph
from app.infrastructure.security import decrypt_secret
from app.domain.ports.repositories import ITelegramRepository, IAuthRepository
import httpx
from langchain_core.messages import HumanMessage, AIMessage

logger = logging.getLogger(__name__)

class TelegramUseCases:
    def __init__(self, telegram_repo: ITelegramRepository, auth_repo: IAuthRepository):
        self.telegram_repo = telegram_repo
        self.auth_repo = auth_repo

    async def _get_vendor_by_public_id(self, session: Any, vendor_public_id: str) -> Optional[User]:
        if vendor_public_id.isdigit():
            return await self.auth_repo.get_user_by_id(session, int(vendor_public_id))
        return await self.auth_repo.get_user_by_email(session, vendor_public_id)

    def _extract_message(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        msg = payload.get("message")
        if not msg:
            return None
        chat = msg.get("chat") or {}
        text = msg.get("text")
        if not (chat and text):
            return None
        return {"chat_id": str(chat.get("id")), "text": text}

    async def process_webhook(
        self, 
        session: Any, 
        vendor_public_id: str, 
        webhook_secret: str, 
        payload: Dict[str, Any]
    ) -> Dict[str, bool]:
        vendor = await self._get_vendor_by_public_id(session, vendor_public_id)
        if not vendor:
            raise HTTPException(status_code=404, detail="vendor_not_found")

        integration = await self.telegram_repo.get_by_vendor_id(session, vendor.id)
        if (
            not integration
            or not integration.is_active
            or integration.state == "deleted"
            or integration.webhook_secret != webhook_secret
        ):
            raise HTTPException(status_code=403, detail="unauthorized_webhook")

        message = self._extract_message(payload)
        if not message:
            return {"ok": True}

        chat_id = message["chat_id"]
        text = message["text"]

        # TODO: Move Customer lookup to a ICustomerRepository
        from sqlmodel import select
        cust_res = await session.execute(select(Customer).where(Customer.telegram_chat_id == chat_id))
        customer = cust_res.scalar_one_or_none()
        customer_id = customer.id if customer else None

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
                result = await app.ainvoke({"messages": [HumanMessage(content=text)]}, config)
                msgs = result.get("messages", []) if isinstance(result, dict) else []
                for m in reversed(msgs):
                    if isinstance(m, AIMessage) and m.content:
                        if "QA Notification" not in str(m.content):
                            reply_text = str(m.content)
                            break
                success = True
            except Exception as e:
                logger.exception({"event": "telegram.webhook.error", "vendor_id": vendor.id, "chat_id": chat_id})
                integration.last_error = str(e)[:500]
                session.add(integration)
                await session.commit()

        duration_ms = int((time.monotonic() - start) * 1000)
        
        # Registrar métrica de auditoría
        metric = AuditLog(
            user_id=vendor.id,
            agent_name="TelegramWebhook",
            action="telegram_webhook_metric",
            details=f"vendor_id={vendor.id}|chat_id={chat_id}|success={success}|duration_ms={duration_ms}",
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        session.add(metric)
        await session.commit()

        # Enviar respuesta al usuario vía API de Telegram
        if reply_text:
            try:
                token = decrypt_secret(integration.bot_token_encrypted)
                if token:
                    async with httpx.AsyncClient(timeout=10) as client:
                        await client.post(
                            f"https://api.telegram.org/bot{token}/sendMessage",
                            json={"chat_id": chat_id, "text": reply_text},
                        )
            except Exception as e:
                logger.error(f"Error sending telegram response: {e}")

        return {"ok": success}

    async def get_status(self, session: Any, vendor_id: int) -> Dict[str, Any]:
        integration = await self.telegram_repo.get_by_vendor_id(session, vendor_id)
        if not integration:
            return {
                "is_active": False,
                "state": "not_configured",
                "bot_username": None,
                "last_error": None
            }
        
        return {
            "is_active": integration.is_active,
            "state": integration.state,
            "bot_username": integration.bot_username,
            "last_error": integration.last_error,
            "updated_at": integration.updated_at
        }

    async def get_mtproto_status(self, session: Any, vendor_id: int) -> Dict[str, Any]:
        from app.infrastructure.adapters.telegram_mtproto import mtproto_manager
        
        is_connected = await mtproto_manager.is_connected(vendor_id)
        
        # Intentar obtener info de la sesión desde la DB
        from app.domain.models.telegram import VendorMtprotoSession
        from sqlmodel import select
        res = await session.execute(select(VendorMtprotoSession).where(VendorMtprotoSession.vendor_id == vendor_id))
        sess = res.scalar_one_or_none()

        return {
            "is_connected": is_connected,
            "enabled": sess.enabled if sess else False,
            "phone": sess.phone if sess else None,
            "last_active": sess.updated_at if sess else None
        }
