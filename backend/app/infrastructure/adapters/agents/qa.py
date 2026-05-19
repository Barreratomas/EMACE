from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.infrastructure.adapters.llm import get_llm
from app.application.state import SupervisorState
from app.infrastructure.adapters.vector.client import get_qdrant_client
from app.infrastructure.adapters.rag.embeddings import get_embeddings
import uuid

from langchain_core.runnables import RunnableConfig

# LLM de QA
llm = get_llm(role="qa", temperature=0)
embeddings = get_embeddings()
client = get_qdrant_client()

def qa_agent(state: SupervisorState, config: RunnableConfig):
    """
    Nodo de Quality Assurance (QA).
    Revisa el último mensaje generado por un agente.
    - Si es seguro y correcto -> Pasa (retorna mensaje tal cual, o con sello de calidad).
    - Si falla -> Retorna feedback para corrección y GUARDA LECCIÓN.
    """
    # Extraemos user_id del config
    user_id = config.get("configurable", {}).get("user_id")
    
    messages = state["messages"]
    last_message = messages[-1]
    
    # Si el último mensaje es del usuario, no hay nada que validar (es input)
    if isinstance(last_message, HumanMessage):
        return {"messages": []}

    # NUEVO: Si el último mensaje ya es una notificación de QA, evitamos el bucle infinito
    if isinstance(last_message, SystemMessage) and "QA Notification" in str(last_message.content):
        return {"messages": []}

    # Extraer contenido y contexto
    agent_response = last_message.content
    
    # Contexto completo de la conversación (últimos 6 mensajes)
    context_history = ""
    for m in messages[-6:-1]:
        role = "Usuario" if isinstance(m, HumanMessage) else "Agente"
        if isinstance(m, SystemMessage): continue
        context_history += f"{role}: {m.content}\n"

    # Buscamos el último mensaje del usuario para la pregunta actual
    user_query = "Unknown"
    for m in reversed(messages[:-1]):
        if isinstance(m, HumanMessage):
            user_query = m.content
            break

    # Prompt de Evaluación
    system_prompt = """Eres el Agente de Calidad (QA). Tu trabajo es auditar las respuestas de los agentes antes de que lleguen al usuario.
    
    CRITERIO DE CONTEXTO (MUY IMPORTANTE):
    - NO rechaces respuestas por ser "ambiguas" si el historial de la conversación aclara el contexto.
    - Si el usuario dice "pasalo a inactivo" y justo antes hablaron del producto "1k2", es CORRECTO que el agente asuma que se refiere a "1k2".
    - El agente NO necesita pedir confirmación constante si la instrucción es clara dentro del flujo de la charla.
    
    Criterios de Aprobación:
    1. Veracidad: No debe contener alucinaciones (inventar datos que NO están en el historial ni en las herramientas).
    2. Seguridad: No revelar datos sensibles.
    3. Utilidad: Responder a lo solicitado.
    4. Fluidez: Evitar bucles de preguntas si la respuesta ya se dio o el contexto es obvio.

    Salida esperada (JSON):
    {{
        "approved": boolean,
        "feedback": "string (motivo del rechazo o sugerencia)",
        "lesson_learned": "string (regla general abstraída del error, si aplica, o null)"
    }}
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", f"HISTORIAL RECIENTE:\n{context_history}\n\nÚLTIMA PREGUNTA: {user_query}\nRESPUESTA A VALIDAR: {agent_response}")
    ])
    
    chain = prompt | llm | JsonOutputParser()
    
    try:
        result = chain.invoke({})
        
        if result["approved"]:
            # Aprobado: Agregamos una señal explícita para el Supervisor
            print(f"✅ QA Aprobado.")
            # Retornamos un mensaje de sistema indicando aprobación para que el Supervisor sepa que puede terminar
            return {"messages": [SystemMessage(content=f"QA Notification: The last response from the agent was APPROVED. If this answers the user's question, route to FINISH.")]}
        else:
            # Rechazado:
            print(f"❌ QA Rechazado: {result['feedback']}")
            
            # 1. Guardar Lección Aprendida (si existe)
            if result.get("lesson_learned"):
                lesson = result["lesson_learned"]
                print(f"📚 Aprendiendo lección: {lesson}")
                
                # Guardar en Qdrant
                vector = embeddings.embed_query(lesson)
                client.upsert(
                    collection_name="lessons_learned",
                    points=[{
                        "id": str(uuid.uuid4()),
                        "vector": vector,
                        "payload": {
                            "page_content": lesson, 
                            "source": "qa_feedback",
                            "user_id": user_id
                        }
                    }]
                )
            
            # 2. Retornar Feedback como mensaje del sistema para que el Supervisor/Agente lo vea
            # Reemplazamos el último mensaje (que estaba mal) con una instrucción de corrección?
            # O mejor, agregamos un mensaje de "System" indicando el error.
            # En LangGraph, agregar mensaje es lo estándar.
            
            # NOTA: Para simplificar el flujo en Fase 5, si QA rechaza, 
            # enviamos un mensaje de ERROR que el Supervisor deberá manejar (o el usuario verá como 'Hubo un error interno, reintentando...').
            # Pero idealmente, el Supervisor debería ver esto y re-enrutar.
            
            feedback_msg = f"[QA RECHAZÓ TU RESPUESTA]: {result['feedback']}. \nCONTEXTO APRENDIDO: {result.get('lesson_learned', '')}"
            
            # Retornamos un mensaje de tipo SystemMessage para que sea interno y no se muestre al usuario
            return {"messages": [SystemMessage(content=feedback_msg)]}
            
    except Exception as e:
        print(f"⚠️ Error en QA: {e}")
        # En caso de error del QA, dejamos pasar por seguridad (fail-open) o bloqueamos (fail-closed).
        # Fail-open para no detener el servicio en demo.
        return {"messages": []}
