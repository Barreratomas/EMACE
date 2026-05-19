from typing import Literal, List, Union, Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from app.infrastructure.adapters.llm import get_llm
from app.application.state import SupervisorState
from app.domain.prompts import SUPERVISOR_SYSTEM_PROMPT
import json

from langchain_core.runnables import RunnableConfig

# Definimos los agentes especialistas disponibles y sus permisos requeridos
MEMBER_PERMISSIONS = {
    "Billing": "billing:access",
    "Tech": "tech:access",
    "Sales": "sales:access",
    "CustomerSupport": "customer:access",
    "Inventory": "inventory:access"
}

# Permisos especiales para clientes (Telegram)
CUSTOMER_PERMISSIONS = ["customer:access", "billing:access"] # Solo pueden ver catálogo/soporte y facturas/compras
MEMBERS = list(MEMBER_PERMISSIONS.keys())

class RouteResponse(BaseModel):
    """Estructura de decisión para el supervisor."""
    reasoning: str = Field(
        description="Explicación breve de por qué se eligió este trabajador, basada en el historial de la conversación y las reglas."
    )
    confidence: float = Field(
        description="Nivel de confianza (0.0 a 1.0) en esta decisión de ruteo. Si es bajo (< 0.5), considera si falta información.",
        ge=0.0,
        le=1.0
    )
    next: List[Literal["Billing", "Tech", "Sales", "CustomerSupport", "Inventory", "FINISH"]] = Field(
        description="El trabajador o lista de trabajadores que deben actuar a continuación. Usa ['FINISH'] si la conversación ha terminado."
    )

llm = get_llm(role="supervisor", temperature=0)

async def supervisor_agent(state: SupervisorState, config: RunnableConfig):
    """
    Nodo del Supervisor: Decide qué agente ejecutar a continuación.
    Usa Structured Outputs para garantizar JSON válido y evitar alucinaciones de texto.
    """
    # Extraemos info del estado
    user_info = state.get("user_info", {})
    user_id = user_info.get("id")
    user_role = user_info.get("role", "customer")
    user_permissions = user_info.get("permissions", [])
    user_name = user_info.get("name", "Usuario")
    
    # --- RBAC: Filtrar miembros disponibles ---
    # Si el usuario es 'admin' o 'vendor', tiene acceso a gestión.
    if user_role in ["admin", "vendor"]:
        available_members = MEMBERS
    elif user_role == "customer":
        available_members = [
            m for m in MEMBERS 
            if MEMBER_PERMISSIONS[m] in CUSTOMER_PERMISSIONS
        ]
    else:
        available_members = [
            m for m in MEMBERS 
            if MEMBER_PERMISSIONS[m] in user_permissions
        ]

    # --- Renderizar Prompt con Contexto de Usuario ---
    system_prompt = SUPERVISOR_SYSTEM_PROMPT.format(
        members=", ".join(available_members),
        user_name=user_name,
        user_role=user_role,
        user_permissions=", ".join(user_permissions) if user_permissions else "Ninguno"
    )
    
    # Si no hay miembros disponibles...
    if not available_members:
        return {
            "next": "FINISH", 
            "messages": [AIMessage(content=f"Lo siento {user_name}, no tienes permisos para acceder a ninguna de las herramientas.")]
        }

    messages = state["messages"]
    
    # --- HARD CHECK: Si el último mensaje es una aprobación de QA, TERMINAR ---
    # Esto evita que el LLM ignore la regla de FINISH tras aprobación.
    if messages and isinstance(messages[-1], SystemMessage) and "QA Notification: The last response from the agent was APPROVED" in str(messages[-1].content):
        print("✅ Detección forzada de QA APPROVED. Finalizando flujo.")
        return {"next": "FINISH"}

    # --- REGLA DE EMERGENCIA: Si el último mensaje es del usuario, RESETEAR ruteo ---
    # Esto evita que el supervisor se quede pegado en un bucle de QA si el usuario manda algo nuevo.
    if isinstance(messages[-1], HumanMessage):
        print(f"🆕 Nuevo mensaje de usuario detectado. Reiniciando ruteo.")
    elif len(messages) > 1 and isinstance(messages[-2], HumanMessage):
        # Si el penúltimo fue humano y el último es un AI que falló QA, priorizar la intención del humano.
        pass

    # Lógica de ruteo con el LLM
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="messages"),
        ("human", "Basado en la conversación anterior y el perfil del usuario, ¿quién debe actuar a continuación? Responde con el JSON de ruteo."),
    ])
    
    # Evitamos with_structured_output por incompatibilidad con StepFun (Error 400)
    # Usamos el LLM directamente y parseamos manualmente el JSON
    chain = prompt | llm
    
    try:
        response = await chain.ainvoke({"messages": messages})
        content = response.content.strip()
        
        # LOG de la respuesta cruda para debug (solo en consola)
        print(f"🔍 Supervisor Raw Output: {content}")
        
        # Intentar extraer JSON si el modelo incluyó texto extra
        import re
        import json
        
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            try:
                # Limpiar posibles caracteres extraños antes/después del JSON
                json_str = json_str.strip()
                data = json.loads(json_str)
                
                # Validamos que tenga la estructura mínima
                next_node = data.get("next")
                if isinstance(next_node, list):
                    next_node = next_node[0] if next_node else "FINISH"
                
                # NORMALIZACIÓN FINAL: Si ya se aprobó algo pero el LLM quiere seguir, forzar FINISH
                # (Doble chequeo por si el LLM alucina un ruteo extra)
                for m in reversed(messages):
                    if isinstance(m, SystemMessage) and "QA Notification: The last response from the agent was APPROVED" in str(m.content):
                        # Si encontramos una aprobación y no hay un mensaje humano posterior, forzar FINISH
                        # Buscamos si hay un HumanMessage después de esa aprobación
                        found_human_after = False
                        idx = messages.index(m)
                        for after_m in messages[idx+1:]:
                            if isinstance(after_m, HumanMessage):
                                found_human_after = True
                                break
                        if not found_human_after:
                            print("➡️ Supervisor intentó repetir ruteo tras aprobación. Forzando FINISH.")
                            return {"next": "FINISH"}

                # Normalización: Si el modelo respondió con un string pero no es un miembro válido
                if next_node not in available_members and next_node != "FINISH":
                    # Intentar buscar el nombre de un miembro en el string
                    for m in available_members:
                        if m.lower() in str(next_node).lower():
                            next_node = m
                            break
                    else:
                        # Si no hay match claro, y hay razonamiento, intentamos inferir
                        reasoning = data.get("reasoning", "").lower()
                        for m in available_members:
                            if m.lower() in reasoning:
                                next_node = m
                                break
                        else:
                            next_node = "FINISH"

                # Validación RBAC: ¿el nodo elegido está entre los permitidos?
                if next_node != "FINISH" and next_node not in available_members:
                    print(f"⚠️ Supervisor intentó rutear a {next_node} sin permisos. Forzando FINISH.")
                    return {"next": "FINISH"}
                    
                print(f"➡️ Supervisor decidió: {next_node}")
                return {"next": next_node or "FINISH"}
            except json.JSONDecodeError:
                print(f"❌ Error al decodificar JSON del Supervisor: {json_str}")
        
        # Fallback si no hay JSON claro pero menciona un miembro
        for member in available_members:
            if member.lower() in content.lower():
                print(f"➡️ Supervisor decidió (fallback): {member}")
                return {"next": member}
                
        print(f"➡️ Supervisor decidió (final fallback): FINISH")
        return {"next": "FINISH"}
        
    except Exception as e:
        print(f"❌ Error crítico en ruteo del Supervisor: {e}")
        return {"next": "FINISH"}
