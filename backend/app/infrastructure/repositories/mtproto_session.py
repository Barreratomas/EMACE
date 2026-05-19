from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.domain.models import VendorMtprotoSession


class MtprotoSessionRepository:
    async def get_by_vendor_id(self, session: AsyncSession, vendor_id: int) -> Optional[VendorMtprotoSession]:
        result = await session.execute(
            select(VendorMtprotoSession).where(VendorMtprotoSession.vendor_id == vendor_id)
        )
        return result.scalar_one_or_none()

    async def upsert(
        self,
        session: AsyncSession,
        vendor_id: int,
        **fields,
    ) -> VendorMtprotoSession:
        existing = await self.get_by_vendor_id(session, vendor_id)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if existing:
            for k, v in fields.items():
                setattr(existing, k, v)
            existing.updated_at = now
            session.add(existing)
            await session.commit()
            await session.refresh(existing)
            return existing
        record = VendorMtprotoSession(vendor_id=vendor_id, **fields, created_at=now, updated_at=now)
        session.add(record)
        await session.commit()
        await session.refresh(record)
        return record


mtproto_session_repo = MtprotoSessionRepository()
