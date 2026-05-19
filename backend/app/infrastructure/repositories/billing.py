from typing import Optional, Any, Dict
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.domain.models import VendorAccessState, BillingEvent, VendorAccessAudit, Invoice, Customer, Order
import logging
logger = logging.getLogger(__name__)

def _serialize(obj: Any) -> Any:
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize(i) for i in obj]
    return obj

from app.domain.ports.repositories import IBillingRepository

class BillingRepository(IBillingRepository):
    async def get_access_state(self, session: AsyncSession, vendor_id: int) -> Optional[VendorAccessState]:
        result = await session.execute(select(VendorAccessState).where(VendorAccessState.vendor_id == vendor_id))
        return result.scalars().first()

    async def upsert_access_state(self, session: AsyncSession, vendor_id: int, updates: Dict[str, Any], actor_user_id: Optional[int] = None) -> VendorAccessState:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        state = await self.get_access_state(session, vendor_id)
        old_state = None
        if not state:
            state = VendorAccessState(
                vendor_id=vendor_id,
                access_mode=updates.get("access_mode", "subscription"),
                source=updates.get("source", "trial"),
                valid_until=updates.get("valid_until"),
                subscription_id_mp=updates.get("subscription_id_mp"),
                created_at=now
            )
            session.add(state)
            await session.flush()
        else:
            old_state = {
                "access_mode": state.access_mode,
                "source": state.source,
                "valid_until": state.valid_until.isoformat() if state.valid_until else None,
                "subscription_id_mp": state.subscription_id_mp
            }
            for k, v in updates.items():
                setattr(state, k, v)
            session.add(state)
        await session.flush()

        new_state = {
            "access_mode": state.access_mode,
            "source": state.source,
            "valid_until": state.valid_until.isoformat() if state.valid_until else None,
            "subscription_id_mp": state.subscription_id_mp
        }
        audit = VendorAccessAudit(
            vendor_id=vendor_id,
            actor_user_id=actor_user_id,
            action=updates.get("_action", "update_access_state"),
            old_state=old_state,
            new_state=new_state,
            created_at=now
        )
        session.add(audit)
        await session.commit()
        await session.refresh(state)
        try:
            logger.info({
                "event": "billing.access_state.updated",
                "vendor_id": vendor_id,
                "action": updates.get("_action", "update_access_state"),
                "old": old_state or {},
                "new": new_state,
            })
        except Exception:
            # logging must never break the flow
            pass
        return state

    async def save_billing_event(self, session: AsyncSession, vendor_id: int, event_type: str, mp_event_id: Optional[str], raw_payload: Optional[dict], normalized: Optional[dict]) -> BillingEvent:
        ev = BillingEvent(
            vendor_id=vendor_id,
            event_type=event_type,
            mp_event_id=mp_event_id,
            raw_payload=raw_payload,
            normalized=_serialize(normalized) if normalized is not None else None,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        session.add(ev)
        await session.commit()
        await session.refresh(ev)
        try:
            logger.info({
                "event": "billing.event.recorded",
                "vendor_id": vendor_id,
                "type": event_type,
                "mp_event_id": mp_event_id,
            })
        except Exception:
            pass
        return ev

    async def find_event_by_mp_id(self, session: AsyncSession, mp_event_id: str) -> Optional[BillingEvent]:
        result = await session.execute(select(BillingEvent).where(BillingEvent.mp_event_id == mp_event_id))
        return result.scalars().first()

    async def get_paid_invoices_summary(self, session: AsyncSession, user_id: int, since: Optional[datetime] = None) -> Dict[str, Any]:
        query = select(
            func.count(Invoice.id),
            func.coalesce(func.sum(Invoice.amount), 0.0),
        ).where(
            Invoice.user_id == user_id,
            Invoice.status == "paid",
        )
        if since:
            query = query.where(Invoice.issued_at >= since)
        result = await session.execute(query)
        count, total = result.one()
        return {"count": count, "total": float(total)}

    async def count_customers(self, session: AsyncSession, user_id: int) -> int:
        result = await session.execute(
            select(func.count(Customer.id)).where(Customer.user_id == user_id)
        )
        return result.scalar() or 0

    async def get_unpaid_invoices_summary(self, session: AsyncSession, user_id: int) -> Dict[str, Any]:
        query = select(
            func.count(Invoice.id),
            func.coalesce(func.sum(Invoice.amount), 0.0),
        ).where(
            Invoice.user_id == user_id,
            Invoice.status != "paid",
        )
        result = await session.execute(query)
        count, total = result.one()
        return {"count": count, "total": float(total)}

    async def count_orders_by_status(self, session: AsyncSession, user_id: int, status: str, since: Optional[datetime] = None) -> int:
        query = select(func.count(Order.id)).where(
            Order.user_id == user_id,
            Order.status == status,
        )
        if since:
            query = query.where(Order.created_at >= since)
        result = await session.execute(query)
        return result.scalar() or 0
