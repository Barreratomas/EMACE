import re
from typing import List, Dict, Any, Callable, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig

from app.application.state import SupervisorState
from app.infrastructure.adapters.llm import get_llm
from app.infrastructure.adapters.agents.router_node import router_node
from app.infrastructure.adapters.agents.tool_node import tool_node
from app.infrastructure.adapters.agents.llm_node import llm_node
from app.infrastructure.adapters.agents.rag_node import rag_node

def clean_message_history(messages: list, role: str) -> list:
    """
    Lógica profesional de filtrado de mensajes:
    1. Preserva la integridad de tool_calls.
    2. Convierte notificaciones internas de QA en instrucciones de sistema.
    3. Mantiene el campo 'name' para identificar actores.
    4. EVITA MODIFICACIÓN IN-PLACE para no corromper el estado global.
    """
    sanitized = []
    for msg in messages:
        # Crear una copia para evitar efectos secundarios en el estado global
        new_msg = msg.copy()
        
        # Convertir mensajes de rechazo de QA en instrucciones directas
        if isinstance(new_msg, (AIMessage, SystemMessage)) and "[QA RECHAZÓ TU RESPUESTA]" in str(new_msg.content):
            sanitized.append(SystemMessage(content=f"CORRECCIÓN REQUERIDA: {new_msg.content}"))
            continue
            
        # Si es un mensaje de este mismo agente, nos aseguramos de que mantenga su nombre
        if isinstance(new_msg, AIMessage) and not getattr(new_msg, "name", None):
            new_msg.name = role

        # Limpieza básica de contenido sin afectar el objeto original en el estado
        if hasattr(new_msg, "content") and isinstance(new_msg.content, str):
            new_msg.content = re.sub(r"^\[.*?\]\s*", "", new_msg.content).strip()
            
        sanitized.append(new_msg)
    return sanitized

def create_explicit_specialist_node(role: str, tools: List[Any], system_prompt: str):
    """
    Factory profesional en la capa de Application para construir subgrafos de agentes especialistas.
    Sigue el plan de modernización de resolver.md eliminando ReAct loops implícitos.
    """
    # 1. Mapeo de herramientas para el ToolNode
    tools_map = {t.name: t for t in tools}
    tools_schema = [{"name": t.name, "description": t.description} for t in tools]

    # 2. Definir los nodos locales envolviendo los adaptadores de infraestructura
    async def local_rag(state: SupervisorState, config: RunnableConfig):
        return await rag_node(state, config)

    async def local_router(state: SupervisorState, config: RunnableConfig):
        # Limpieza de historial (Lógica de Aplicación)
        sanitized_messages = clean_message_history(state["messages"], role)
        # Inyectar el rol en el config para que el adaptador sepa qué LLM usar
        config["configurable"] = {**config.get("configurable", {}), "role": role}
        return await router_node(state, config, tools_schema, sanitized_messages)

    async def local_tools(state: SupervisorState, config: RunnableConfig):
        return await tool_node(state, config, tools_map)

    async def local_llm(state: SupervisorState, config: RunnableConfig):
        # Limpieza de historial (Lógica de Aplicación)
        sanitized_messages = clean_message_history(state["messages"], role)
        
        user_info = state.get("user_info", {})
        try:
            # Reemplazo de variables de contexto en el prompt (Lógica de Aplicación)
            full_system_prompt = system_prompt.format(
                user_name=user_info.get("name", "Usuario"),
                user_role=user_info.get("role", "customer")
            )
        except:
            full_system_prompt = system_prompt

        config["configurable"] = {**config.get("configurable", {}), "role": role}
        return await llm_node(state, config, full_system_prompt, sanitized_messages)

    def should_continue(state: SupervisorState) -> str:
        """
        Lógica condicional programática (Conditional Edge).
        Inspecciona los mensajes para decidir si continuar con el LLM o volver al Router.
        """
        messages = state.get("messages", [])
        if not messages:
            return "Router"
            
        last_message = messages[-1]
        
        if isinstance(last_message, ToolMessage):
            content = str(last_message.content).lower()
            # Control de flujo basado en contenido del mensaje de herramienta
            if any(word in content for word in ["éxito", "guardado", "creado", "actualizado", "success", "saved"]):
                return "LLM"
            if "error" in content:
                return "Router"
                
        return "Router"

    # 3. Construcción del Grafo (Responsabilidad de la capa de Application)
    builder = StateGraph(SupervisorState)
    
    builder.add_node("RAG", local_rag)
    builder.add_node("Router", local_router)
    builder.add_node("Tools", local_tools)
    builder.add_node("LLM", local_llm)

    builder.set_entry_point("RAG")
    builder.add_edge("RAG", "Router")
    
    builder.add_conditional_edges(
        "Router",
        lambda state: state.get("next_step", "RESPONDER"),
        {
            "TOOL": "Tools",
            "RESPONDER": "LLM"
        }
    )
    
    builder.add_conditional_edges(
        "Tools",
        should_continue,
        {
            "Router": "Router",
            "LLM": "LLM"
        }
    )
    
    builder.add_edge("LLM", END)

    return builder.compile()
