import os
import pytest
from httpx import AsyncClient


requires_env = pytest.mark.skipif(
    not (
        os.getenv("STAGING_BASE_URL")
        and os.getenv("STAGING_VENDOR_EMAIL")
        and os.getenv("STAGING_VENDOR_PASSWORD")
    ),
    reason="Variables de entorno STAGING_BASE_URL, STAGING_VENDOR_EMAIL y STAGING_VENDOR_PASSWORD requeridas",
)


@pytest.mark.staging
@requires_env
@pytest.mark.asyncio
async def test_mtproto_staging_smoke_status_and_rollback():
    base_url = os.environ["STAGING_BASE_URL"].rstrip("/")
    email = os.environ["STAGING_VENDOR_EMAIL"]
    password = os.environ["STAGING_VENDOR_PASSWORD"]

    async with AsyncClient(base_url=base_url, timeout=20) as ac:
        r = await ac.post("/api/v1/auth/login", data={"username": email, "password": password})
        assert r.status_code == 200
        tokens = r.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        r = await ac.get(
            "/api/v1/vendors/me/integrations/telegram/mtproto/status",
            headers=headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert "mtproto_status" in body
        assert "mtproto_enabled" in body

        if body.get("mtproto_enabled") is True:
            r = await ac.post(
                "/api/v1/vendors/me/integrations/telegram/mtproto/disable",
                headers=headers,
            )
            assert r.status_code == 200

        r = await ac.post(
            "/api/v1/vendors/me/integrations/telegram/mtproto/revoke",
            headers=headers,
        )
        assert r.status_code == 200
        rb = r.json()
        assert rb.get("ok") is True

        r = await ac.get(
            "/api/v1/vendors/me/integrations/telegram/mtproto/status",
            headers=headers,
        )
        assert r.status_code == 200
        body = r.json()
        assert body.get("mtproto_enabled") is False
        assert body.get("mtproto_status") in ("inactive", "awaiting_code", "ready")
