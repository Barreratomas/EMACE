from typing import Annotated, List, Optional, Sequence, TypedDict, Union
import operator
from langchain_core.messages import BaseMessage

# Definimos el estado global del grafo
class SupervisorState(TypedDict):
    # La lista de mensajes es append-only (se agregan nuevos mensajes)
    messages: Annotated[Sequence[BaseMessage], operator.add]
    # El siguiente nodo a ejecutar (decidido por el Supervisor)
    next: str
    # Información del usuario actual (Inyectada desde el backend)
    user_info: Optional[dict] = None
    # Historial de conversación para contexto (puede ser redundante con messages, pero útil si se estructura diferente)
    # Por ahora usamos messages estándar de LangGraph.
