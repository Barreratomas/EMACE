from typing import List, Optional, Any
from sqlalchemy import select, func
from app.domain.models import AuditLog
from app.domain.ports.repositories import IAuditRepository

class AuditRepository(IAuditRepository):
    async def get_logs_by_user(self, session: Any, user_id: int, limit: int = 50, offset: int = 0) -> List[AuditLog]:
        result = await session.execute(
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(AuditLog.timestamp.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_logs_by_user(self, session: Any, user_id: int, since: Optional[Any] = None) -> int:
        query = select(func.count(AuditLog.id)).where(AuditLog.user_id == user_id)
        if since:
            query = query.where(AuditLog.timestamp >= since)
        result = await session.execute(query)
        return result.scalar() or 0

    async def count_distinct_agents(self, session: Any, user_id: int, since: Optional[Any] = None) -> int:
        query = select(func.count(func.distinct(AuditLog.agent_name))).where(AuditLog.user_id == user_id)
        if since:
            query = query.where(AuditLog.timestamp >= since)
        result = await session.execute(query)
        return result.scalar() or 0

    async def save_log(self, session: Any, log: AuditLog) -> AuditLog:
        session.add(log)
        await session.commit()
        await session.refresh(log)
        return log
