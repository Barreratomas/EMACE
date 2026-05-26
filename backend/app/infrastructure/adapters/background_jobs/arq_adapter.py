from typing import Any, Dict, Optional
from arq import create_pool
from arq.connections import RedisSettings
from app.domain.ports.background_jobs import IBackgroundJobPort
from app.infrastructure.config import Settings

class ArqAdapter(IBackgroundJobPort):
    def __init__(self, settings: Settings):
        self.settings = settings
        self.redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
        self._pool = None

    async def _get_pool(self):
        if self._pool is None:
            self._pool = await create_pool(self.redis_settings)
        return self._pool

    async def enqueue_task(self, task_name: str, *args, **kwargs) -> str:
        """Encola una tarea en Redis usando ARQ"""
        pool = await self._get_pool()
        job = await pool.enqueue_job(task_name, *args, **kwargs)
        return job.job_id

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene el estado de la tarea desde Redis"""
        pool = await self._get_pool()
        job = await pool.get_job(task_id)
        if not job:
            return None
            
        status = await job.status()
        info = await job.info()
        
        return {
            "task_id": task_id,
            "status": status,
            "enqueue_time": info.enqueue_time if info else None,
            "function": info.function if info else None,
        }
