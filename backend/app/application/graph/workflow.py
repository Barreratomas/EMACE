from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from app.application.state import SupervisorState
from app.infrastructure.adapters.llm import get_llm
from app.infrastructure.adapters.agents.supervisor import supervisor_agent, MEMBERS
from app.infrastructure.adapters.agents.qa import qa_agent
from app.infrastructure.adapters.rag.retriever import retriever

# Subgrafos
from app.application.graph.subgraphs.billing import billing_graph

# Agentes Especialistas
from app.infrastructure.adapters.agents.tech import tech_node
from app.infrastructure.adapters.agents.sales import sales_node, customer_support_node
from app.infrastructure.adapters.agents.inventory import inventory_node

# --- Grafo Principal (Orquestador) ---
builder = StateGraph(SupervisorState)

# 1. Nodos
builder.add_node("Supervisor", supervisor_agent)
builder.add_node("Tech", tech_node)
builder.add_node("Sales", sales_node)
builder.add_node("CustomerSupport", customer_support_node)
builder.add_node("Inventory", inventory_node)
builder.add_node("QA", qa_agent)

# AQUI LA MAGIA: El nodo "Billing" ahora es un Subgrafo entero
builder.add_node("Billing", billing_graph)

# 2. Edges
# Todos pasan por QA antes de volver al Supervisor
builder.add_edge("Tech", "QA")
builder.add_edge("Sales", "QA")
builder.add_edge("CustomerSupport", "QA")
builder.add_edge("Inventory", "QA")
builder.add_edge("Billing", "QA") 

builder.add_edge("QA", "Supervisor")

# 3. Routing
builder.add_conditional_edges(
    "Supervisor",
    lambda state: state["next"],
    {
        "Billing": "Billing", 
        "Tech": "Tech",
        "Sales": "Sales",
        "CustomerSupport": "CustomerSupport",
        "Inventory": "Inventory",
        "FINISH": END
    }
)

builder.set_entry_point("Supervisor")
workflow = builder.compile() # Exportamos el grafo compilado
