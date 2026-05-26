from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class IBackgroundJobPort(ABC):
    @abstractmethod
    async def enqueue_task(self, task_name: str, *args, **kwargs) -> str:
        """
        Encola una tarea para su procesamiento en segundo plano.
        
        Args:
            task_name: Nombre de la función registrada en el worker.
            *args: Argumentos posicionales para la tarea.
            **kwargs: Argumentos de palabra clave para la tarea.
            
        Returns:
            ID de la tarea encolada.
        """
        pass

    @abstractmethod
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el estado actual de una tarea.
        
        Args:
            task_id: ID de la tarea.
            
        Returns:
            Diccionario con el estado o None si no existe.
        """
        pass
