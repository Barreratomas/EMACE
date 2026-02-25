from __future__ import annotations
import re
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, Optional
from app.core.telegram_mtproto import mtproto_manager
from app.core.database.session import get_async_sessionmaker
from app.core.database.models import AuditLog
from datetime import datetime, timezone
from app.core.config import settings
from app.core.security import encrypt_secret
from app.repositories.telegram_integration import telegram_integration_repo
from uuid import uuid4
import httpx
from prometheus_client import Counter, Histogram

logger = logging.getLogger(__name__)

BOTFATHER_ID = 93372553

AUTOCREATE_TOTAL = Counter(
    "mtproto_bot_autocreate_total",
    "Auto-creation outcomes",
    ["status"],
)
AUTOCREATE_DURATION = Histogram(
    "mtproto_bot_autocreate_duration_seconds",
    "Duration of bot auto-creation per vendor",
    ["vendor_id"],
)

@dataclass
class BotCreationState:
    vendor_id: int
    bot_name: str
    username_hint: str
    status: str = "idle"
    expected: Optional[str] = None
    retries: int = 0
    token: Optional[str] = None
    last_error: Optional[str] = None
    started_at: float = field(default_factory=lambda: time.time())

@dataclass
class BotDeletionState:
    vendor_id: int
    bot_username: str
    status: str = "idle"
    expected: Optional[str] = None
    last_error: Optional[str] = None
    started_at: float = field(default_factory=lambda: time.time())


def _normalize_username(u: str) -> str:
    print("botfather_orchestrator._normalize_username", u)
    s = re.sub(r"[^a-zA-Z0-9_]", "", u)
    if not s.lower().endswith("bot"):
        s = f"{s}_bot"
    return s


def _extract_token(text: str) -> Optional[str]:
    print("botfather_orchestrator._extract_token called")
    m = re.search(r"([0-9]{6,}:[A-Za-z0-9_-]{20,})", text)
    if m:
        return m.group(1)
    return None


class BotFatherOrchestrator:
    def __init__(self) -> None:
        print("botfather_orchestrator.__init__")
        self._states: Dict[int, BotCreationState] = {}
        self._deletion_states: Dict[int, BotDeletionState] = {}

    async def _persist_state(self, vendor_id: int, st: BotCreationState | BotDeletionState) -> None:
        print("botfather_orchestrator._persist_state", vendor_id, st.status, st.expected)
        action = "bot_auto_create_state" if isinstance(st, BotCreationState) else "bot_hard_delete_state"
        try:
            async_session = get_async_sessionmaker()
            async with async_session() as session:
                log = AuditLog(
                    user_id=vendor_id,
                    agent_name="BotFatherOrchestrator",
                    action=action,
                    details=f"status={st.status}|expected={st.expected}|error={st.last_error or ''}",
                    timestamp=datetime.now(timezone.utc),
                )
                session.add(log)
                await session.commit()
        except Exception as e:
            logger.warning({"event": "botfather.persist.error", "vendor_id": vendor_id, "error": str(e)[:200]})

    def has_active(self, vendor_id: int) -> bool:
        print("botfather_orchestrator.has_active", vendor_id)
        st = self._states.get(vendor_id)
        dst = self._deletion_states.get(vendor_id)
        
        if st and st.status not in ("completed", "failed"):
            return True
        if dst and dst.status not in ("completed", "failed"):
            return True
            
        return False

    def get_state(self, vendor_id: int) -> Optional[BotCreationState]:
        print("botfather_orchestrator.get_state", vendor_id)
        return self._states.get(vendor_id)

    def clear_vendor_states(self, vendor_id: int) -> None:
        """Limpia cualquier estado de orquestación para el vendor."""
        print("botfather_orchestrator.clear_vendor_states", vendor_id)
        self._states.pop(vendor_id, None)
        self._deletion_states.pop(vendor_id, None)

    async def start_auto_create(self, vendor_id: int, bot_name: str, username_hint: str) -> None:
        print("botfather_orchestrator.start_auto_create", vendor_id, bot_name, username_hint)
        uname = _normalize_username(username_hint.strip())
        st = BotCreationState(
            vendor_id=vendor_id,
            bot_name=bot_name.strip(),
            username_hint=uname,
            status="sent_newbot",
            expected="ask_name",
        )
        self._states[vendor_id] = st
        try:
            await mtproto_manager.send_message(vendor_id, BOTFATHER_ID, "/newbot")
            await self._persist_state(vendor_id, st)
        except Exception as e:
            st.status = "failed"
            st.last_error = f"send_newbot_error:{str(e)[:80]}"
            logger.error({"event": "botfather.start.error", "vendor_id": vendor_id, "error": str(e)[:200]})
            await self._persist_state(vendor_id, st)
            try:
                AUTOCREATE_TOTAL.labels(status="error").inc()
                AUTOCREATE_DURATION.labels(vendor_id=str(vendor_id)).observe(max(0.0, time.time() - st.started_at))
            except Exception:
                pass

    async def start_bot_deletion(self, vendor_id: int, bot_username: str) -> None:
        """Inicia el proceso de eliminación de un bot en BotFather."""
        print("botfather_orchestrator.start_bot_deletion", vendor_id, bot_username)
        dst = BotDeletionState(
            vendor_id=vendor_id,
            bot_username=bot_username,
            status="sent_deletebot",
            expected="ask_which_bot",
        )
        self._deletion_states[vendor_id] = dst
        try:
            await mtproto_manager.send_message(vendor_id, BOTFATHER_ID, "/deletebot")
            await self._persist_state(vendor_id, dst)
        except Exception as e:
            dst.status = "failed"
            dst.last_error = f"send_deletebot_error:{str(e)[:80]}"
            logger.error({"event": "botfather.delete_start.error", "vendor_id": vendor_id, "error": str(e)[:200]})
            await self._persist_state(vendor_id, dst)

    async def on_botfather_message(self, vendor_id: int, text: str, meta: dict) -> None:
        print("botfather_orchestrator.on_botfather_message", vendor_id, text[:80])
        st = self._states.get(vendor_id)
        dst = self._deletion_states.get(vendor_id)
        low = text.lower()

        # Priorizar orquestación de creación si existe
        if st and st.status not in ("completed", "failed"):
            await self._handle_creation_step(st, low, text)
            return

        # Si no hay creación, manejar eliminación
        if dst and dst.status not in ("completed", "failed"):
            await self._handle_deletion_step(dst, low, text)
            return

    async def _handle_creation_step(self, st: BotCreationState, low: str, text: str) -> None:
        vendor_id = st.vendor_id
        try:
            if st.expected == "ask_name":
                if "name" in low or "nombre" in low:
                    await mtproto_manager.send_message(vendor_id, BOTFATHER_ID, st.bot_name)
                    st.status = "sent_name"
                    st.expected = "ask_username"
                    await self._persist_state(vendor_id, st)
                    return
            elif st.expected == "ask_username":
                if "username" in low or "nombre de usuario" in low:
                    await mtproto_manager.send_message(vendor_id, BOTFATHER_ID, st.username_hint)
                    st.status = "sent_username"
                    st.expected = "waiting_token"
                    await self._persist_state(vendor_id, st)
                    return
                if "is already taken" in low or "is taken" in low or "ya está en uso" in low or "ocupado" in low:
                    st.retries += 1
                    if st.retries > 3:
                        st.status = "failed"
                        st.last_error = "username_taken_exceeded"
                        await self._persist_state(vendor_id, st)
                        return
                    suffix = f"_{int(time.time())%1000}"
                    st.username_hint = _normalize_username(st.username_hint + suffix)
                    await mtproto_manager.send_message(vendor_id, BOTFATHER_ID, st.username_hint)
                    st.status = "sent_username"
                    st.expected = "waiting_token"
                    await self._persist_state(vendor_id, st)
                    return
            elif st.expected == "waiting_token":
                tok = _extract_token(text)
                if tok:
                    st.token = tok
                    st.status = "completed"
                    st.expected = None
                    logger.info({"event": "botfather.token.captured", "vendor_id": vendor_id})
                    await self._persist_state(vendor_id, st)
                    try:
                        AUTOCREATE_TOTAL.labels(status="success").inc()
                        AUTOCREATE_DURATION.labels(vendor_id=str(vendor_id)).observe(max(0.0, time.time() - st.started_at))
                    except Exception:
                        pass
                    # Validar token y persistir integración + webhook (si hay base pública)
                    bot_username: Optional[str] = None
                    try:
                        async with httpx.AsyncClient(timeout=10) as client:
                            resp = await client.get(f"https://api.telegram.org/bot{tok}/getMe")
                            if resp.status_code == 200:
                                data = resp.json()
                                if data.get("ok") and data.get("result", {}).get("username"):
                                    bot_username = data["result"]["username"]
                    except httpx.HTTPError as e:
                        logger.warning({"event": "botfather.getme.error", "vendor_id": vendor_id, "error": str(e)[:200]})
                    if bot_username:
                        try:
                            enc = encrypt_secret(tok)
                            secret = uuid4().hex
                            async_session = get_async_sessionmaker()
                            async with async_session() as session:
                                await telegram_integration_repo.upsert(
                                    session=session,
                                    vendor_id=vendor_id,
                                    bot_username=bot_username,
                                    bot_token_encrypted=enc,
                                    webhook_secret=secret,
                                )
                                base = settings.EFFECTIVE_TELEGRAM_PUBLIC_BASE_URL
                                if base:
                                    base = str(base).rstrip("/")
                                    url = f"{base}{settings.API_V1_STR}/telegram/webhook/{vendor_id}/{secret}"
                                    try:
                                        async with httpx.AsyncClient(timeout=10) as client:
                                            await client.post(
                                                f"https://api.telegram.org/bot{tok}/setWebhook",
                                                json={"url": url},
                                            )
                                    except httpx.HTTPError as e:
                                        logger.warning({"event": "botfather.setwebhook.error", "vendor_id": vendor_id, "error": str(e)[:200]})
                        except Exception as e:
                            logger.error({"event": "botfather.persist.credentials.error", "vendor_id": vendor_id, "error": str(e)[:200]})
                    return
                if "too many attempts" in low or "limit" in low:
                    st.status = "failed"
                    st.last_error = "creation_limited"
                    await self._persist_state(vendor_id, st)
                    try:
                        AUTOCREATE_TOTAL.labels(status="error").inc()
                        AUTOCREATE_DURATION.labels(vendor_id=str(vendor_id)).observe(max(0.0, time.time() - st.started_at))
                    except Exception:
                        pass
                    return
        except Exception as e:
            st.status = "failed"
            st.last_error = f"orchestration_error:{str(e)[:80]}"
            logger.error({"event": "botfather.on_message.error", "vendor_id": vendor_id, "error": str(e)[:200]})
            await self._persist_state(vendor_id, st)
            try:
                AUTOCREATE_TOTAL.labels(status="error").inc()
                AUTOCREATE_DURATION.labels(vendor_id=str(vendor_id)).observe(max(0.0, time.time() - st.started_at))
            except Exception:
                pass

    async def _handle_deletion_step(self, dst: BotDeletionState, low: str, text: str) -> None:
        vendor_id = dst.vendor_id
        try:
            if dst.expected == "ask_which_bot":
                if "choose" in low or "elija" in low or "seleccione" in low or "which bot" in low:
                    await mtproto_manager.send_message(vendor_id, BOTFATHER_ID, f"@{dst.bot_username}")
                    dst.status = "sent_bot_to_delete"
                    dst.expected = "ask_confirmation"
                    await self._persist_state(vendor_id, dst)
                    return
            elif dst.expected == "ask_confirmation":
                if "are you sure" in low or "estás seguro" in low or "totally sure" in low:
                    await mtproto_manager.send_message(vendor_id, BOTFATHER_ID, "Yes, I am totally sure.")
                    dst.status = "sent_confirmation"
                    dst.expected = "waiting_final_confirmation"
                    await self._persist_state(vendor_id, dst)
                    return
            elif dst.expected == "waiting_final_confirmation":
                if "done" in low or "gone" in low or "eliminado" in low or "borrado" in low:
                    dst.status = "completed"
                    dst.expected = None
                    logger.info({"event": "botfather.deletion.completed", "vendor_id": vendor_id, "bot": dst.bot_username})
                    await self._persist_state(vendor_id, dst)
                    return
        except Exception as e:
            dst.status = "failed"
            dst.last_error = f"deletion_orchestration_error:{str(e)[:80]}"
            logger.error({"event": "botfather.deletion.error", "vendor_id": vendor_id, "error": str(e)[:200]})
            await self._persist_state(vendor_id, dst)


botfather_orchestrator = BotFatherOrchestrator()
