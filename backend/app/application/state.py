from typing import Annotated, List, Optional, Sequence, TypedDict, Union, Dict, Any
import operator
from langchain_core.messages import BaseMessage

# Definimos el estado global del grafo
class SupervisorState(TypedDict):
    # La lista de mensajes es append-only (se agregan nuevos mensajes)
    messages: Annotated[Sequence[BaseMessage], operator.add]
    # El siguiente nodo a ejecutar (decidido por el Supervisor)
    next: str
    # Información del usuario actual (Inyectada desde el backend)
    user_info: Optional[Dict[str, Any]] = None
    # Resultados de herramientas (para workflow explícito)
    tool_results: Optional[List[Dict[str, Any]]] = None
    # Contexto recuperado (RAG)
    context: Optional[str] = None
    # Paso específico dentro de un flujo (opcional)
    next_step: Optional[str] = None
