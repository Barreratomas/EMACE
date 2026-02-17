from datetime import datetime, timezone
from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.models import VendorAccessAudit


class TelegramIntegrationAuditService:
    async def log_integration_change(
        self,
        session: AsyncSession,
        vendor_id: int,
        actor_user_id: Optional[int],
        action: str,
        old_state: Optional[Dict[str, Any]],
        new_state: Optional[Dict[str, Any]],
    ) -> None:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        audit = VendorAccessAudit(
            vendor_id=vendor_id,
            actor_user_id=actor_user_id,
            action=action,
            old_state=old_state,
            new_state=new_state,
            created_at=now,
        )
        session.add(audit)
        await session.commit()


telegram_integration_audit = TelegramIntegrationAuditService()

