import pytest
from types import SimpleNamespace
from app.core.config import settings
from app.api.v1.endpoints.billing import verify_mp_signature


@pytest.mark.asyncio
async def test_verify_mp_signature_ok(monkeypatch):
    monkeypatch.setattr(settings, "MP_WEBHOOK_SECRET", "secret")
    body = b'{"id":"123"}'
    import hmac, hashlib
    digest = hmac.new(b"secret", body, hashlib.sha256).hexdigest()
    request = SimpleNamespace(headers={"x-signature": digest})
    assert verify_mp_signature(request, body) is True


@pytest.mark.asyncio
async def test_verify_mp_signature_fail(monkeypatch):
    monkeypatch.setattr(settings, "MP_WEBHOOK_SECRET", "secret")
    body = b'{"id":"123"}'
    request = SimpleNamespace(headers={"x-signature": "invalid"})
    assert verify_mp_signature(request, body) is False
