from typing import Optional, List
from datetime import datetime, timezone

from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.models import VendorTelegramIntegration


class TelegramIntegrationRepository:
    async def get_by_vendor_id(self, session: AsyncSession, vendor_id: int) -> Optional[VendorTelegramIntegration]:
        """Obtiene la integración por vendor_id, incluyendo las eliminadas para poder reactivarlas."""
        result = await session.execute(
            select(VendorTelegramIntegration).where(
                VendorTelegramIntegration.vendor_id == vendor_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_bot_username(self, session: AsyncSession, bot_username: str) -> Optional[VendorTelegramIntegration]:
        result = await session.execute(
            select(VendorTelegramIntegration).where(
                VendorTelegramIntegration.bot_username == bot_username,
                VendorTelegramIntegration.state != "deleted",
            )
        )
        return result.scalar_one_or_none()

    async def get_all_active(self, session: AsyncSession) -> List[VendorTelegramIntegration]:
        """Obtiene todas las integraciones activas."""
        result = await session.execute(
            select(VendorTelegramIntegration).where(
                VendorTelegramIntegration.is_active == True,
                VendorTelegramIntegration.state == "active"
            )
        )
        return list(result.scalars().all())

    async def upsert(
        self,
        session: AsyncSession,
        vendor_id: int,
        bot_username: str,
        bot_token_encrypted: str,
        webhook_secret: str,
    ) -> VendorTelegramIntegration:
        existing = await self.get_by_vendor_id(session, vendor_id)
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        if existing:
            existing.bot_username = bot_username
            existing.bot_token_encrypted = bot_token_encrypted
            existing.webhook_secret = webhook_secret
            existing.is_active = True
            existing.state = "active"
            existing.paused_at = None
            existing.deleted_at = None
            existing.paused_by_user_id = None
            existing.updated_at = now
            session.add(existing)
            await session.commit()
            await session.refresh(existing)
            return existing

        integration = VendorTelegramIntegration(
            vendor_id=vendor_id,
            bot_username=bot_username,
            bot_token_encrypted=bot_token_encrypted,
            webhook_secret=webhook_secret,
            is_active=True,
            state="active",
            paused_at=None,
            deleted_at=None,
            paused_by_user_id=None,
            created_at=now,
            updated_at=now,
        )
        session.add(integration)
        await session.commit()
        await session.refresh(integration)
        return integration


telegram_integration_repo = TelegramIntegrationRepository()
