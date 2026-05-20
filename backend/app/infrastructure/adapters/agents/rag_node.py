from typing import Dict, Any
from langchain_core.runnables import RunnableConfig
from app.application.state import SupervisorState
from app.infrastructure.adapters.rag.retriever import retriever

async def rag_node(state: SupervisorState, config: RunnableConfig):
    """
    Nodo de recuperación (RAG).
    Busca contexto relevante basado en el último mensaje del usuario.
    """
    messages = state["messages"]
    
    # Buscar el último mensaje humano
    query = ""
    for m in reversed(messages):
        if m.type == "human":
            query = m.content
            break
            
    if not query:
        return {"context": ""}
        
    print(f"🔍 RAG: Buscando contexto para: {query[:50]}...")
    try:
        # Usamos el retriever configurado
        docs = await retriever.ainvoke(query)
        context = "\n\n".join([d.page_content for d in docs])
        return {"context": context}
    except Exception as e:
        print(f"❌ Error en rag_node: {e}")
        return {"context": ""}
