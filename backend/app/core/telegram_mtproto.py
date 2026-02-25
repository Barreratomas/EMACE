from __future__ import annotations

from typing import Awaitable, Callable, Optional, Dict, Any, List
from dataclasses import dataclass
import asyncio
import logging
import time
import random
import json

from telethon import TelegramClient, events  # type: ignore
from telethon.errors import FloodWaitError  # type: ignore
from telethon.sessions import StringSession  # type: ignore

from app.core.config import settings
from app.core.security import decrypt_secret
from app.core.database.session import get_async_sessionmaker
from app.core.database.models import VendorMtprotoSession
from app.repositories.mtproto_session import mtproto_session_repo
from prometheus_client import Gauge, Counter


logger = logging.getLogger(__name__)


MessageHandler = Callable[[int, str, Dict[str, Any]], Awaitable[None]]


@dataclass
class MtprotoVendorConfig:
    vendor_id: int
    api_id: int
    api_hash: str
    session_encrypted: str
    allowed_chats: List[str]


class MtprotoClientManager:
    def __init__(self) -> None:
        self._clients: Dict[int, TelegramClient] = {}
        self._locks: Dict[int, asyncio.Lock] = {}
        self._handler: Optional[MessageHandler] = None
        self._retries: Dict[int, Dict[str, float]] = {}
        self._send_locks: Dict[int, asyncio.Lock] = {}
        self._next_send_ts: Dict[int, float] = {}
        self._sessions_active = Gauge(
            "mtproto_sessions_active",
            "MTProto sessions with active connection",
            ["vendor_id"],
        )
        self._reconnects_total = Counter(
            "mtproto_reconnects_total",
            "MTProto reconnects per vendor",
            ["vendor_id"],
        )
        self._events_total = Counter(
            "mtproto_events_rate",
            "MTProto events per vendor and direction",
            ["vendor_id", "direction"],
        )
        self._floodwait_seconds = Gauge(
            "mtproto_floodwait_seconds",
            "Last FloodWait duration in seconds per vendor",
            ["vendor_id"],
        )

    def set_handler(self, handler: MessageHandler) -> None:
        self._handler = handler

    async def _build_config_for_vendor(self, vendor_id: int) -> Optional[MtprotoVendorConfig]:
        if not settings.TELEGRAM_MTPROTO_API_ID or not settings.TELEGRAM_MTPROTO_API_HASH:
            return None
        async_session = get_async_sessionmaker()
        async with async_session() as session:
            record = await mtproto_session_repo.get_by_vendor_id(session, vendor_id)
            if not record or not record.enabled or not record.session_encrypted:
                return None
            try:
                session_str = decrypt_secret(record.session_encrypted)
            except Exception as e:
                logger.error(
                    {
                        "event": "mtproto.decrypt_error",
                        "vendor_id": vendor_id,
                        "error": str(e)[:200],
                    }
                )
                return None
            allowed = record.allowed_chats or []
            return MtprotoVendorConfig(
                vendor_id=vendor_id,
                api_id=int(settings.TELEGRAM_MTPROTO_API_ID),
                api_hash=settings.TELEGRAM_MTPROTO_API_HASH,
                session_encrypted=session_str,
                allowed_chats=allowed,
            )

    async def ensure_connected(self, vendor_id: int) -> Optional[TelegramClient]:
        rs = self._retries.setdefault(vendor_id, {"fail": 0.0, "next": 0.0})
        now = time.time()
        if now < rs["next"]:
            return self._clients.get(vendor_id)
        lock = self._locks.setdefault(vendor_id, asyncio.Lock())
        async with lock:
            if vendor_id in self._clients:
                return self._clients[vendor_id]
            cfg = await self._build_config_for_vendor(vendor_id)
            if not cfg:
                return None
            client = TelegramClient(
                session=StringSession(cfg.session_encrypted),
                api_id=cfg.api_id,
                api_hash=cfg.api_hash,
            )

            @client.on(events.NewMessage)
            async def handler(event):  # type: ignore
                if not self._handler:
                    return
                chat = await event.get_chat()
                chat_id = getattr(chat, "id", None)
                if chat_id is None:
                    return
                chat_username = getattr(chat, "username", None)
                is_botfather = (str(chat_id) == "93372553") or (str(chat_username).lower() == "botfather")
                if cfg.allowed_chats and str(chat_id) not in cfg.allowed_chats and not is_botfather:
                    return
                text = event.raw_text or ""
                meta = {
                    "chat_id": str(chat_id),
                    "chat_username": chat_username or None,
                    "message_id": event.id,
                    "date": event.date.isoformat() if event.date else None,
                }
                await self._handler(cfg.vendor_id, text, meta)
                self._events_total.labels(str(cfg.vendor_id), "in").inc()

            try:
                await client.connect()
                self._clients[vendor_id] = client
                rs["fail"] = 0.0
                rs["next"] = 0.0
                vlabel = str(vendor_id)
                self._sessions_active.labels(vlabel).set(1)
                if rs.get("fail", 0.0) > 0.0:
                    self._reconnects_total.labels(vlabel).inc()
                logger.info(
                    {"event": "mtproto.connected", "vendor_id": vendor_id}
                )
                return client
            except Exception as e:
                rs["fail"] = rs.get("fail", 0.0) + 1.0
                backoff = min(300.0, (2.0 ** rs["fail"]) + random.uniform(0, 1))
                rs["next"] = now + backoff
                logger.error(
                    {"event": "mtproto.connect_error", "vendor_id": vendor_id, "error": str(e)[:200], "backoff_sec": backoff}
                )
                return None

    async def send_message(self, vendor_id: int, chat_id: int | str, text: str) -> None:
        client = await self.ensure_connected(vendor_id)
        if not client:
            return
        slock = self._send_locks.setdefault(vendor_id, asyncio.Lock())
        async with slock:
            wait_until = self._next_send_ts.get(vendor_id, 0.0)
            now = time.time()
            if wait_until > now:
                await asyncio.sleep(wait_until - now)
            try:
                entity: int | str
                s = str(chat_id).strip().lower()
                if s == "botfather" or s == "93372553":
                    entity = "botfather"
                else:
                    if isinstance(chat_id, int):
                        entity = chat_id
                    else:
                        entity = int(s) if s.isdigit() else s
                await client.send_message(entity=entity, message=text)
                self._next_send_ts[vendor_id] = time.time() + 0.2
                self._events_total.labels(str(vendor_id), "out").inc()
            except FloodWaitError as e:  # type: ignore
                logger.warning(
                    {
                        "event": "mtproto.flood_wait",
                        "vendor_id": vendor_id,
                        "seconds": getattr(e, "seconds", None),
                    }
                )
                seconds = getattr(e, "seconds", None)
                if seconds is None:
                    seconds = 5
                dur = float(seconds)
                self._floodwait_seconds.labels(str(vendor_id)).set(dur)
                self._next_send_ts[vendor_id] = time.time() + dur + random.uniform(0, 1)
            except Exception as e:
                logger.error(
                    {"event": "mtproto.send_error", "vendor_id": vendor_id, "error": str(e)[:200]}
                )

    async def disconnect_vendor(self, vendor_id: int) -> None:
        client = self._clients.pop(vendor_id, None)
        if client:
            try:
                await client.disconnect()
            except Exception:
                pass
        self._sessions_active.labels(str(vendor_id)).set(0)

    async def shutdown(self) -> None:
        tasks = [self.disconnect_vendor(v_id) for v_id in list(self._clients.keys())]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def create_pending_session(self, phone_number: str) -> str:
        if not settings.TELEGRAM_MTPROTO_API_ID or not settings.TELEGRAM_MTPROTO_API_HASH:
            raise RuntimeError("mtproto_api_credentials_missing")
        client = TelegramClient(
            session=StringSession(),
            api_id=int(settings.TELEGRAM_MTPROTO_API_ID),
            api_hash=settings.TELEGRAM_MTPROTO_API_HASH,
        )
        await client.connect()
        try:
            result = await client.send_code_request(phone_number)
            phone_code_hash = getattr(result, "phone_code_hash", None)
            session_str = client.session.save()
        finally:
            await client.disconnect()
        payload: Dict[str, Any] = {"session": session_str}
        if phone_code_hash:
            payload["phone_code_hash"] = phone_code_hash
        return json.dumps(payload)

    async def finalize_session(self, session_str: str, phone_number: str, code: str) -> str:
        if not settings.TELEGRAM_MTPROTO_API_ID or not settings.TELEGRAM_MTPROTO_API_HASH:
            raise RuntimeError("mtproto_api_credentials_missing")

        raw_session = session_str
        phone_code_hash: Optional[str] = None
        try:
            data = json.loads(session_str)
            if isinstance(data, dict):
                raw_session = data.get("session") or ""
                phone_code_hash = data.get("phone_code_hash") or None
        except Exception:
            raw_session = session_str

        client = TelegramClient(
            session=StringSession(raw_session),
            api_id=int(settings.TELEGRAM_MTPROTO_API_ID),
            api_hash=settings.TELEGRAM_MTPROTO_API_HASH,
        )
        await client.connect()
        try:
            if phone_code_hash:
                await client.sign_in(phone=phone_number, code=code, phone_code_hash=phone_code_hash)
            else:
                await client.sign_in(phone=phone_number, code=code)
            final_session = client.session.save()
        finally:
            await client.disconnect()
        return final_session

    async def list_bots_from_father(self, vendor_id: int) -> List[Dict[str, str]]:
        """
        Usa la sesión MTProto del vendor para listar sus bots enviando /mybots a BotFather.
        Esta es una aproximación, ya que BotFather responde con un teclado interactivo.
        """
        client = await self.ensure_connected(vendor_id)
        if not client:
            return []

        # Enviar /mybots a BotFather
        from telethon.tl.types import InputPeerUser
        # BotFather ID: 93372553
        botfather = await client.get_input_entity("botfather")
        
        # Necesitamos capturar la respuesta. Como es asíncrono y por eventos,
        # una forma simple es esperar un poco y ver los últimos mensajes.
        await client.send_message(botfather, "/mybots")
        
        # Esperar a que BotFather responda (usualmente rápido)
        await asyncio.sleep(2)
        
        bots = []
        async for message in client.iter_messages(botfather, limit=5):
            # BotFather suele responder con una lista de botones con los usernames
            if message.reply_markup:
                from telethon.tl.types import ReplyInlineMarkup, KeyboardButtonCallback
                if hasattr(message.reply_markup, 'rows'):
                    for row in message.reply_markup.rows:
                        for button in row.buttons:
                            if hasattr(button, 'text') and button.text.startswith('@'):
                                bots.append({
                                    "username": button.text.replace('@', ''),
                                    "display_name": button.text
                                })
            
            # También puede estar en el texto si no hay botones (menos común)
            if not bots and "/mybots" not in message.text:
                import re
                found = re.findall(r'@([a-zA-Z0-9_]{5,32}bot)', message.text, re.IGNORECASE)
                for b in found:
                    bots.append({"username": b, "display_name": f"@{b}"})
        
        return bots


mtproto_manager = MtprotoClientManager()
