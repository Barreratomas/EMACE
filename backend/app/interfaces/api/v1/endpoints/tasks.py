from fastapi import APIRouter, Depends, HTTPException
from typing import Any, Dict
from app.interfaces.api.deps import get_current_user, get_background_job_port
from app.domain.models import User
from app.domain.ports.background_jobs import IBackgroundJobPort

router = APIRouter()

@router.get("/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
    background_job_port: IBackgroundJobPort = Depends(get_background_job_port)
) -> Dict[str, Any]:
    """
    Obtiene el estado de una tarea en segundo plano.
    """
    status = await background_job_port.get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    # Nota: En una implementación más estricta, podríamos verificar que la tarea 
    # pertenezca al usuario actual si guardamos esa relación en una DB.
    # Por ahora, ARQ guarda el estado en Redis de forma volátil.
    
    return status
