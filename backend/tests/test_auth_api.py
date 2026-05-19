import pytest
import asyncio
from datetime import datetime
from httpx import AsyncClient, ASGITransport
from app.interfaces.api.main import app
from app.infrastructure.config import settings
from app.infrastructure.database.session import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.models import User, Role

@pytest.mark.asyncio
async def test_auth_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Register
        unique_id = datetime.now().strftime("%Y%m%d%H%M%S")
        register_data = {
            "email": f"test_{unique_id}@example.com",
            "password": "Password123!@#",
            "name": f"Test User {unique_id}"
        }
        response = await ac.post("/api/v1/auth/register", json=register_data)
        if response.status_code != 201:
            print(f"Register failed: {response.status_code} - {response.text}")
        assert response.status_code == 201
        assert response.json()["email"] == register_data["email"]

        # 2. Login
        login_data = {
            "username": register_data["email"],
            "password": register_data["password"]
        }
        response = await ac.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        tokens = response.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        # 3. Get Me
        headers = {"Authorization": f"Bearer {access_token}"}
        response = await ac.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        assert response.json()["email"] == register_data["email"]

        # 4. Update Profile
        update_data = {"name": "Updated Name"}
        response = await ac.patch("/api/v1/auth/me", json=update_data, headers=headers)
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"

        # 5. Refresh Token
        response = await ac.post(f"/api/v1/auth/refresh?token_str={refresh_token}")
        assert response.status_code == 200
        new_tokens = response.json()
        assert "access_token" in new_tokens
        assert new_tokens["access_token"] != access_token

        # 6. Change Password
        change_pwd_data = {
            "old_password": register_data["password"],
            "new_password": "NewPassword123!@#"
        }
        response = await ac.post("/api/v1/auth/me/change-password", json=change_pwd_data, headers=headers)
        assert response.status_code == 200

        # 7. Login with new password
        login_data["password"] = change_pwd_data["new_password"]
        response = await ac.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == 200
        
    print("✅ All auth tests passed!")

if __name__ == "__main__":
    asyncio.run(test_auth_flow())
