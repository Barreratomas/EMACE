from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.application.state import SupervisorState
from app.infrastructure.adapters.llm import get_llm
from app.infrastructure.adapters.tools.billing import get_client_invoices, check_invoice_status
from app.infrastructure.adapters.rag.retriever import retriever
from app.application.graph.specialist_factory import create_explicit_specialist_node

from langchain_core.runnables import RunnableConfig

# Subgrafo de Facturación
# En lugar de ser un solo agente, ahora es un flujo: [Research] -> [Analyst] -> [Formatter]

def billing_subgraph_builder():
    """
    Construye un subgrafo especializado para facturación.
    Demuestra escalabilidad al romper una tarea compleja en pasos discretos.
    """
    
    # Nodo A: Investigador (Usa el nuevo factory explícito)
    researcher_node = create_explicit_specialist_node(
        role="billing",
        tools=[get_client_invoices, check_invoice_status],
        system_prompt="Eres un Investigador de Facturación. Tu ÚNICO trabajo es usar herramientas para buscar los datos crudos solicitados. No intentes explicar, solo extrae la data."
    )

    # Nodo B: Analista (Interpreta datos sin tools)
    def analyst_node(state: SupervisorState, config: RunnableConfig):
        print("   📊 [Billing Subgraph] Analyst interpretando resultados...")
        llm = get_llm(role="billing", temperature=0.3) # Un poco más creativo para explicar
        
        last_msg = state["messages"][-1]
        analysis_prompt = f"""
        Analiza los datos crudos proporcionados por el investigador:
        {last_msg.content}
        
        Genera una respuesta amable y clara para el usuario final.
        Si hay deudas, menciona el monto exacto.
        """
        
        response = llm.invoke([HumanMessage(content=analysis_prompt)])
        # No agregamos prefijos manuales
        return {"messages": [response]}

    # 3. Construir Grafo Local
    sub_builder = StateGraph(SupervisorState)
    sub_builder.add_node("Researcher", researcher_node)
    sub_builder.add_node("Analyst", analyst_node)
    
    # Flujo lineal: Start -> Researcher -> Analyst -> End
    sub_builder.set_entry_point("Researcher")
    sub_builder.add_edge("Researcher", "Analyst")
    sub_builder.add_edge("Analyst", END)
    
    return sub_builder.compile()

# Instancia exportable
billing_graph = billing_subgraph_builder()
