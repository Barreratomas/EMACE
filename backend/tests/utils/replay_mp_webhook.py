import asyncio
from httpx import AsyncClient, ASGITransport
from app.api.main import app


async def main():
    payload = {"type": "payment", "metadata": {}, "data": {"id": "demo"}}
    headers = {"x-request-id": "mp-replay-1"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post("/api/v1/billing/webhooks/mp", json=payload, headers=headers)
        print(r.status_code, r.json())
        r = await ac.post("/api/v1/billing/webhooks/mp", json=payload, headers=headers)
        print(r.status_code, r.json())


if __name__ == "__main__":
    asyncio.run(main())
