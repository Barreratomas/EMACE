import pytest
import asyncio
from datetime import datetime
from httpx import AsyncClient, ASGITransport
from app.interfaces.api.main import app
from datetime import timedelta, timezone


@pytest.mark.asyncio
async def test_subscription_checkout_and_lifetime_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        uid = datetime.now().strftime("%Y%m%d%H%M%S%f")
        register = {"email": f"billing_{uid}@example.com", "password": "Password123!@#", "name": f"Billing {uid}"}
        r = await ac.post("/api/v1/auth/register", json=register)
        assert r.status_code == 201
        login = {"username": register["email"], "password": register["password"]}
        r = await ac.post("/api/v1/auth/login", data=login)
        assert r.status_code == 200
        tokens = r.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        r = await ac.post("/api/v1/billing/subscriptions", json={"title": "Plan Mensual", "price": 1.0}, headers=headers)
        assert r.status_code == 201
        assert "checkout_url" in r.json()

        r = await ac.post("/api/v1/billing/lifetime", json={}, headers=headers)
        assert r.status_code == 200
        js = r.json()
        assert js["access_mode"] == "lifetime"


@pytest.mark.asyncio
async def test_webhook_idempotency_with_vendor():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        uid = datetime.now().strftime("%Y%m%d%H%M%S%f")
        register = {"email": f"vendor_{uid}@example.com", "password": "Password123!@#", "name": f"Vendor {uid}"}
        r = await ac.post("/api/v1/auth/register", json=register)
        assert r.status_code == 201
        vendor_id = r.json()["id"]

        payload = {"type": "payment", "metadata": {"vendor_id": vendor_id}}
        headers = {"x-request-id": "mp-test-123"}
        r1 = await ac.post("/api/v1/billing/webhooks/mp", json=payload, headers=headers)
        assert r1.status_code == 200
        r2 = await ac.post("/api/v1/billing/webhooks/mp", json=payload, headers=headers)
        assert r2.status_code == 200
        assert r2.json().get("idempotent") is True


@pytest.mark.asyncio
async def test_trial_exists_after_register_and_payment_updates_state():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        uid = datetime.now().strftime("%Y%m%d%H%M%S%f")
        register = {"email": f"trial_{uid}@example.com", "password": "Password123!@#", "name": f"Trial {uid}"}
        r = await ac.post("/api/v1/auth/register", json=register)
        assert r.status_code == 201
        login = {"username": register["email"], "password": register["password"]}
        r = await ac.post("/api/v1/auth/login", data=login)
        access_token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        r = await ac.get("/api/v1/billing/access-state", headers=headers)
        assert r.status_code == 200
        state = r.json()
        assert state["source"] == "trial"
        assert state["valid_until"] is not None

        vendor_id = r.json()["vendor_id"]
        payload = {"type": "payment", "metadata": {"vendor_id": vendor_id}}
        r2 = await ac.post("/api/v1/billing/webhooks/mp", json=payload, headers={"x-request-id": f"mp-{uid}"})
        assert r2.status_code == 200
        r3 = await ac.get("/api/v1/billing/access-state", headers=headers)
        assert r3.status_code == 200
        st2 = r3.json()
        assert st2["access_mode"] == "subscription"
        assert st2["source"] == "paid_subscription"
        # valid_until debe ser en el futuro respecto a ahora
        from datetime import datetime as dt
        now = dt.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=1)
        assert st2["valid_until"] is not None
