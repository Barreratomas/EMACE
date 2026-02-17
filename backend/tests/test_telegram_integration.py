import pytest
import pytest_asyncio
from datetime import datetime
from typing import Any
from httpx import AsyncClient, ASGITransport
from contextlib import asynccontextmanager

from langchain_core.messages import AIMessage

from app.api.main import app
from app.api.v1.endpoints.telegram import _is_mtproto_allowed
import app.api.v1.endpoints.telegram as telegram_module
from app.core import telegram_mtproto as mtproto_module
from app.core.config import settings
import app.api.main as main_module


class DummyResponse:
    def __init__(self, status_code: int = 200, json_data: dict[str, Any] | None = None):
        self.status_code = status_code
        self._json_data = json_data or {}

    def json(self) -> dict[str, Any]:
        return self._json_data


@pytest_asyncio.fixture(scope="module")
async def telegram_auth_headers() -> dict[str, str]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        uid = datetime.now().strftime("%Y%m%d%H%M%S%f")
        register = {
            "email": f"tg_base_{uid}@example.com",
            "password": "Password123!@#",
            "name": f"TG Base {uid}",
        }
        r = await ac.post("/api/v1/auth/register", json=register)
        assert r.status_code == 201
        login = {"username": register["email"], "password": register["password"]}
        r = await ac.post("/api/v1/auth/login", data=login)
        assert r.status_code == 200
        tokens = r.json()
        return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.mark.asyncio
async def test_telegram_admin_list_requires_admin_role(telegram_auth_headers: dict[str, str]):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get("/api/v1/telegram/admin/integrations", headers=telegram_auth_headers)
        assert r.status_code in (401, 403)


def test_is_mtproto_allowed_disabled(monkeypatch):
    monkeypatch.setattr(settings, "TELEGRAM_MTPROTO_ENABLED", False)
    monkeypatch.setattr(settings, "TELEGRAM_MTPROTO_KILL_SWITCH", False)
    monkeypatch.setattr(settings, "TELEGRAM_MTPROTO_ALLOWED_VENDORS", None)
    assert _is_mtproto_allowed(1) is False


def test_is_mtproto_allowed_kill_switch(monkeypatch):
    monkeypatch.setattr(settings, "TELEGRAM_MTPROTO_ENABLED", True)
    monkeypatch.setattr(settings, "TELEGRAM_MTPROTO_KILL_SWITCH", True)
    monkeypatch.setattr(settings, "TELEGRAM_MTPROTO_ALLOWED_VENDORS", "1,2,3")
    assert _is_mtproto_allowed(1) is False
    assert _is_mtproto_allowed(2) is False


def test_is_mtproto_allowed_all_vendors_when_no_list(monkeypatch):
    monkeypatch.setattr(settings, "TELEGRAM_MTPROTO_ENABLED", True)
    monkeypatch.setattr(settings, "TELEGRAM_MTPROTO_KILL_SWITCH", False)
    monkeypatch.setattr(settings, "TELEGRAM_MTPROTO_ALLOWED_VENDORS", None)
    assert _is_mtproto_allowed(1) is True
    assert _is_mtproto_allowed(999) is True


def test_is_mtproto_allowed_specific_vendors(monkeypatch):
    monkeypatch.setattr(settings, "TELEGRAM_MTPROTO_ENABLED", True)
    monkeypatch.setattr(settings, "TELEGRAM_MTPROTO_KILL_SWITCH", False)
    monkeypatch.setattr(settings, "TELEGRAM_MTPROTO_ALLOWED_VENDORS", "1, 42 , 7")
    assert _is_mtproto_allowed(42) is True
    assert _is_mtproto_allowed(7) is True
    assert _is_mtproto_allowed(2) is False


@pytest.mark.asyncio
async def test_mtproto_consent_unavailable_when_disabled(
    monkeypatch, telegram_auth_headers: dict[str, str]
):
    monkeypatch.setattr(settings, "TELEGRAM_MTPROTO_ENABLED", False)
    monkeypatch.setattr(settings, "TELEGRAM_MTPROTO_KILL_SWITCH", False)
    monkeypatch.setattr(settings, "TELEGRAM_MTPROTO_ALLOWED_VENDORS", None)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post(
            "/api/v1/vendors/me/integrations/telegram/mtproto/consent",
            json={"accepted": True, "terms_version": "v1"},
            headers=telegram_auth_headers,
        )
        assert r.status_code == 503
        assert r.json()["detail"] == "mtproto_unavailable"


@pytest.mark.asyncio
async def test_mtproto_consent_unavailable_when_kill_switch(
    monkeypatch, telegram_auth_headers: dict[str, str]
):
    monkeypatch.setattr(settings, "TELEGRAM_MTPROTO_ENABLED", True)
    monkeypatch.setattr(settings, "TELEGRAM_MTPROTO_KILL_SWITCH", True)
    monkeypatch.setattr(settings, "TELEGRAM_MTPROTO_ALLOWED_VENDORS", None)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post(
            "/api/v1/vendors/me/integrations/telegram/mtproto/consent",
            json={"accepted": True, "terms_version": "v1"},
            headers=telegram_auth_headers,
        )
        assert r.status_code == 503
        assert r.json()["detail"] == "mtproto_unavailable"


@pytest.mark.asyncio
async def test_mtproto_consent_requires_accept_flag(
    monkeypatch, telegram_auth_headers: dict[str, str]
):
    monkeypatch.setattr(settings, "TELEGRAM_MTPROTO_ENABLED", True)
    monkeypatch.setattr(settings, "TELEGRAM_MTPROTO_KILL_SWITCH", False)
    monkeypatch.setattr(settings, "TELEGRAM_MTPROTO_ALLOWED_VENDORS", None)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post(
            "/api/v1/vendors/me/integrations/telegram/mtproto/consent",
            json={"accepted": False, "terms_version": "v1"},
            headers=telegram_auth_headers,
        )
        assert r.status_code == 400
        assert r.json()["detail"] == "consent_not_accepted"


@pytest.mark.asyncio
async def test_mtproto_consent_success(monkeypatch, telegram_auth_headers: dict[str, str]):
    monkeypatch.setattr(settings, "TELEGRAM_MTPROTO_ENABLED", True)
    monkeypatch.setattr(settings, "TELEGRAM_MTPROTO_KILL_SWITCH", False)
    monkeypatch.setattr(settings, "TELEGRAM_MTPROTO_ALLOWED_VENDORS", None)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post(
            "/api/v1/vendors/me/integrations/telegram/mtproto/consent",
            json={"accepted": True, "terms_version": "v-test"},
            headers=telegram_auth_headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["ok"] is True
        assert body["terms_version"] == "v-test"


@pytest.mark.asyncio
async def test_telegram_bot_management_forbidden_for_iam_user():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        uid = datetime.now().strftime("%Y%m%d%H%M%S%f")
        vendor_email = f"vendor_rbac_{uid}@example.com"
        vendor_password = "Password123!@#"
        register = {
            "email": vendor_email,
            "password": vendor_password,
            "name": f"Vendor RBAC {uid}",
        }
        r = await ac.post("/api/v1/auth/register", json=register)
        assert r.status_code == 201
        login = {"username": vendor_email, "password": vendor_password}
        r = await ac.post("/api/v1/auth/login", data=login)
        assert r.status_code == 200
        vendor_tokens = r.json()
        vendor_headers = {"Authorization": f"Bearer {vendor_tokens['access_token']}"}

        iam_email = f"iam_rbac_{uid}@example.com"
        iam_payload = {
            "email": iam_email,
            "password": "Password123!@#",
            "name": f"IAM RBAC {uid}",
        }
        r = await ac.post(
            "/api/v1/iam/users",
            json=iam_payload,
            headers=vendor_headers,
        )
        assert r.status_code == 201

        iam_login_body = {
            "email": iam_email,
            "password": "Password123!@#",
            "vendor_identifier": vendor_email,
        }
        r = await ac.post("/api/v1/auth/login-iam", json=iam_login_body)
        assert r.status_code == 200
        iam_tokens = r.json()
        iam_headers = {"Authorization": f"Bearer {iam_tokens['access_token']}"}

        r = await ac.post(
            "/api/v1/vendors/me/integrations/telegram/bot/pause",
            headers=iam_headers,
        )
        assert r.status_code == 403
        assert r.json()["detail"] == "bot_management_forbidden"


@pytest.mark.asyncio
async def test_mtproto_handler_ignores_non_botfather_messages(monkeypatch):
    monkeypatch.setattr(main_module.settings, "TELEGRAM_MTPROTO_ENABLED", True)
    monkeypatch.setattr(main_module.settings, "TELEGRAM_MTPROTO_KILL_SWITCH", False)

    class DummyMtprotoManager:
        def __init__(self) -> None:
            self.handler = None
            self.sent: list[tuple[int, str, str]] = []

        def set_handler(self, handler) -> None:
            self.handler = handler

        async def send_message(self, vendor_id: int, chat_id: int | str, text: str) -> None:
            self.sent.append((vendor_id, str(chat_id), text))

        async def ensure_connected(self, vendor_id: int) -> None:
            return None

        async def shutdown(self) -> None:
            return None

    dummy_manager = DummyMtprotoManager()

    @asynccontextmanager
    async def dummy_checkpointer():
        yield "dummy_checkpointer"

    monkeypatch.setattr(main_module, "mtproto_manager", dummy_manager)
    monkeypatch.setattr(main_module, "get_postgres_checkpointer", dummy_checkpointer)
    async def _ignored_mtproto_loop():
        return None

    monkeypatch.setattr(main_module.asyncio, "create_task", lambda coro: _ignored_mtproto_loop())

    await main_module.startup_event()

    assert dummy_manager.handler is not None

    handler = dummy_manager.handler
    vendor_id = 123
    meta = {"chat_id": "9999", "message_id": 1}

    await handler(vendor_id, "Hola, esto no es BotFather", meta)

    assert dummy_manager.sent == []


@pytest.mark.asyncio
async def test_mtproto_session_state_transitions_and_serialization(
    monkeypatch, telegram_auth_headers: dict[str, str]
):
    monkeypatch.setattr(settings, "TELEGRAM_MTPROTO_ENABLED", True)
    monkeypatch.setattr(settings, "TELEGRAM_MTPROTO_KILL_SWITCH", False)
    monkeypatch.setattr(settings, "TELEGRAM_MTPROTO_ALLOWED_VENDORS", None)

    monkeypatch.setattr(telegram_module, "encrypt_secret", lambda value: f"enc:{value}")
    monkeypatch.setattr(telegram_module, "decrypt_secret", lambda value: value.replace("enc:", "", 1))

    class FakeRec:
        def __init__(self, vendor_id: int):
            self.vendor_id = vendor_id
            self.session_encrypted: str | None = None
            self.phone_number: str | None = None
            self.status: str = "inactive"
            self.enabled: bool = False
            self.last_error: str | None = None
            self.allowed_chats: list[str] = []
            self.last_heartbeat_at = None

    class FakeRepo:
        def __init__(self) -> None:
            self.records: dict[int, FakeRec] = {}

        async def get_by_vendor_id(self, session: Any, vendor_id: int) -> FakeRec | None:
            return self.records.get(vendor_id)

        async def upsert(self, session: Any, vendor_id: int, **kwargs: Any) -> FakeRec:
            rec = self.records.get(vendor_id) or FakeRec(vendor_id)
            for key, value in kwargs.items():
                setattr(rec, key, value)
            self.records[vendor_id] = rec
            return rec

    fake_repo = FakeRepo()
    monkeypatch.setattr(telegram_module, "mtproto_session_repo", fake_repo)

    async def fake_create_pending_session(phone_number: str) -> str:
        return "pending-session"

    async def fake_finalize_session(pending: str, phone_number: str, code: str) -> str:
        assert pending == "pending-session"
        assert code == "12345"
        return "final-session"

    monkeypatch.setattr(mtproto_module.mtproto_manager, "create_pending_session", fake_create_pending_session)
    monkeypatch.setattr(mtproto_module.mtproto_manager, "finalize_session", fake_finalize_session)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get(
            "/api/v1/vendors/me/integrations/telegram/mtproto/status",
            headers=telegram_auth_headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["mtproto_status"] == "inactive"
        assert body["mtproto_enabled"] is False

        r = await ac.post(
            "/api/v1/vendors/me/integrations/telegram/mtproto/session/init",
            json={"phone_number": "+123456789"},
            headers=telegram_auth_headers,
        )
        assert r.status_code == 202

        r = await ac.get(
            "/api/v1/vendors/me/integrations/telegram/mtproto/status",
            headers=telegram_auth_headers,
        )
        body = r.json()
        assert body["mtproto_status"] == "awaiting_code"
        assert body["mtproto_enabled"] is False

        r = await ac.post(
            "/api/v1/vendors/me/integrations/telegram/mtproto/session/confirm",
            json={"code": "12345"},
            headers=telegram_auth_headers,
        )
        assert r.status_code == 202
        body = r.json()
        assert body["status"] == "ready"

        r = await ac.get(
            "/api/v1/vendors/me/integrations/telegram/mtproto/status",
            headers=telegram_auth_headers,
        )
        body = r.json()
        assert body["mtproto_status"] == "ready"
        assert body["mtproto_enabled"] is False

        r = await ac.post(
            "/api/v1/vendors/me/integrations/telegram/mtproto/enable",
            headers=telegram_auth_headers,
        )
        assert r.status_code == 202
        body = r.json()
        assert body["mtproto_enabled"] is True
        assert body["status"] == "enabled"

        r = await ac.get(
            "/api/v1/vendors/me/integrations/telegram/mtproto/status",
            headers=telegram_auth_headers,
        )
        body = r.json()
        assert body["mtproto_status"] == "enabled"
        assert body["mtproto_enabled"] is True

        r = await ac.post(
            "/api/v1/vendors/me/integrations/telegram/mtproto/disable",
            headers=telegram_auth_headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["mtproto_enabled"] is False
        assert body["status"] == "inactive"

        r = await ac.get(
            "/api/v1/vendors/me/integrations/telegram/mtproto/status",
            headers=telegram_auth_headers,
        )
        body = r.json()
        assert body["mtproto_status"] == "inactive"
        assert body["mtproto_enabled"] is False

        r = await ac.post(
            "/api/v1/vendors/me/integrations/telegram/mtproto/revoke",
            headers=telegram_auth_headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert body["ok"] is True

        r = await ac.post(
            "/api/v1/vendors/me/integrations/telegram/mtproto/enable",
            headers=telegram_auth_headers,
        )
        assert r.status_code == 400
        assert r.json()["detail"] == "session_not_configured"


@pytest.mark.asyncio
async def test_mtproto_send_message_handles_floodwait_and_sets_backoff(monkeypatch):
    manager = mtproto_module.mtproto_manager
    manager._next_send_ts.clear()
    vendor_id = 99

    class DummyFlood(Exception):
        def __init__(self, seconds: int):
            self.seconds = seconds

    class DummyClient:
        def __init__(self) -> None:
            self.calls = 0

        async def send_message(self, entity: int, message: str) -> None:
            self.calls += 1
            raise DummyFlood(7)

    dummy_client = DummyClient()

    async def fake_ensure_connected(v_id: int):
        assert v_id == vendor_id
        return dummy_client

    manager.ensure_connected = fake_ensure_connected  # type: ignore[assignment]

    monkeypatch.setattr("app.core.telegram_mtproto.FloodWaitError", DummyFlood)
    monkeypatch.setattr("app.core.telegram_mtproto.time.time", lambda: 1000.0)
    monkeypatch.setattr("app.core.telegram_mtproto.random.uniform", lambda a, b: 0.0)

    before = manager._next_send_ts.get(vendor_id, 0.0)
    await manager.send_message(vendor_id, 123456, "hola mtproto")
    after = manager._next_send_ts.get(vendor_id, 0.0)

    assert dummy_client.calls == 1
    assert after > before
    assert after == 1007.0
