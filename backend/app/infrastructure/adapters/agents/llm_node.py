from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from app.application.state import SupervisorState
from app.infrastructure.adapters.llm import get_llm

async def llm_node(state: SupervisorState, config: RunnableConfig, system_prompt: str, sanitized_messages: List[BaseMessage] = None):
    """
    Genera la respuesta final del agente especialista.
    Utiliza el contexto recuperado (RAG) si está presente en el estado.
    """
    role = config.get("configurable", {}).get("role", "default")
    llm = get_llm(role=role, temperature=0)
    
    messages = sanitized_messages if sanitized_messages is not None else state["messages"]
    context = state.get("context", "")
    tool_results = state.get("tool_results", [])
    
    # Preparar el prompt del sistema con el contexto
    full_prompt = system_prompt
    if context:
        full_prompt += f"\n\nCONTEXTO RECUPERADO (RAG):\n{context}"
    
    if tool_results:
        results_str = "\n".join([f"Herramienta {r['name']} retornó: {r.get('result', 'Sin resultado')}" for r in tool_results])
        full_prompt += f"\n\nRESULTADOS DE HERRAMIENTAS:\n{results_str}"
        
    prompt = ChatPromptTemplate.from_messages([
        ("system", full_prompt),
        ("placeholder", "{messages}")
    ])
    
    chain = prompt | llm
    
    response = await chain.ainvoke({"messages": messages})
    
    # Marcamos el mensaje con el nombre del agente para trazabilidad
    if isinstance(response, AIMessage):
        response.name = role
        
    return {"messages": [response], "next_step": "FINISH"}
