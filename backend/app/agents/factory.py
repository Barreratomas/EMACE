from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from app.core.state import SupervisorState
from app.core.llm import get_llm
from app.core.rag.retriever import retriever

from langchain_core.runnables import RunnableConfig

def clean_message_history(messages: list, role: str) -> list:
    """
    Lógica profesional de filtrado de mensajes:
    1. Preserva la integridad de tool_calls.
    2. Convierte notificaciones internas de QA en instrucciones de sistema.
    3. Mantiene el campo 'name' para identificar actores.
    4. EVITA MODIFICACIÓN IN-PLACE para no corromper el estado global.
    """
    import re
    from langchain_core.messages import AIMessage, SystemMessage, HumanMessage, ToolMessage
    
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

def create_specialist_node(role: str, tools: list, system_prompt: str):
    """
    Factory profesional para nodos de agentes especialistas.
    """
    llm = get_llm(role=role, temperature=0)
    agent_executor = create_react_agent(llm, tools)
    
    def node_func(state: SupervisorState, config: RunnableConfig):
        print(f"🤖 Agente {role.capitalize()} activo.")
        
        user_info = state.get("user_info", {})
        user_id = user_info.get("id")
        
        # --- GESTIÓN DE CONTEXTO PROFESIONAL ---
        sanitized_messages = clean_message_history(state["messages"], role)
        
        # Inyectar contexto de usuario
        try:
            full_system_prompt = system_prompt.format(
                user_name=user_info.get("name", "Usuario"),
                user_role=user_info.get("role", "customer")
            )
        except:
            full_system_prompt = system_prompt

        # Preparar mensajes para el LLM
        final_messages = [SystemMessage(content=full_system_prompt)] + sanitized_messages
        
        # Ejecutar ReAct
        result = agent_executor.invoke({"messages": final_messages}, config)
        
        # Extraer solo lo nuevo
        new_messages = result["messages"][len(final_messages):]
        
        # Log de herramientas (Opcional, pero útil para debug)
        for msg in new_messages:
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    print(f"🛠️ [{role}] Tool: {tc['name']}")
            if msg.type == "tool":
                print(f"📦 [{role}] Result: {str(msg.content)[:50]}...")

        # Asignar nombre al mensaje de salida para trazabilidad
        for msg in new_messages:
            if isinstance(msg, AIMessage):
                msg.name = role

        return {"messages": new_messages}
    return node_func
    return node_func
