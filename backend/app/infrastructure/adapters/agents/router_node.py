from typing import Dict, Any, List
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from app.application.state import SupervisorState
from app.infrastructure.adapters.llm import get_llm
import json
import re

async def router_node(state: SupervisorState, config: RunnableConfig, tools_schema: List[Dict[str, Any]], sanitized_messages: List[BaseMessage] = None):
    """
    Decide si el agente necesita usar una herramienta o puede responder directamente.
    Recibe el esquema de herramientas disponibles para este especialista.
    """
    role = config.get("configurable", {}).get("role", "default")
    llm = get_llm(role=role, temperature=0)
    
    messages = sanitized_messages if sanitized_messages is not None else state["messages"]
    
    # Prompt para decidir ruteo
    router_prompt = """Eres un router de inteligencia. Tu objetivo es decidir si el usuario necesita una de las herramientas disponibles o si puedes responder directamente.
    
    HERRAMIENTAS DISPONIBLES:
    {tools_description}
    
    INSTRUCCIONES:
    1. Si la consulta del usuario requiere una herramienta, responde con el nombre de la herramienta y los argumentos en formato JSON.
    2. Si puedes responder directamente basado en el contexto actual, responde con "RESPONDER".
    3. Si falta información para usar una herramienta, pide la información necesaria respondiendo con "RESPONDER".
    
    Respuesta esperada (JSON):
    {{
        "decision": "TOOL" | "RESPONDER",
        "tool_name": "nombre_de_la_herramienta" | null,
        "tool_args": {{ ... }} | null,
        "reasoning": "breve explicación"
    }}
    """
    
    tools_description = "\n".join([f"- {t['name']}: {t['description']}" for t in tools_schema])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", router_prompt.format(tools_description=tools_description)),
        ("placeholder", "{messages}")
    ])
    
    chain = prompt | llm
    
    try:
        response = await chain.ainvoke({"messages": messages})
        content = response.content.strip()
        
        # Extraer JSON
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0))
            decision = data.get("decision", "RESPONDER")
            
            if decision == "TOOL" and data.get("tool_name"):
                return {
                    "next_step": "TOOL",
                    "tool_results": [{"name": data["tool_name"], "args": data.get("tool_args", {})}]
                }
        
        return {"next_step": "RESPONDER"}
        
    except Exception as e:
        print(f"❌ Error en router_node: {e}")
        return {"next_step": "RESPONDER"}
