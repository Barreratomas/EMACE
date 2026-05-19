from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from app.infrastructure.adapters.rag.retriever import retriever

@tool
def search_technical_docs(query: str, config: RunnableConfig) -> str:
    """
    Busca información técnica en la base de conocimientos (manuales, guías, documentación).
    Usa esta herramienta para responder preguntas sobre configuración, errores o especificaciones técnicas.
    """
    user_id = config.get("configurable", {}).get("user_id")
    
    try:
        # Pasamos user_id al retriever para filtrar (si aplica)
        results = retriever.search(query, collection="knowledge_base", limit=3, user_id=user_id)
        
        if not results:
            return "No encontré información relevante en la documentación técnica."
            
        response = f"Resultados encontrados para '{query}':\n\n"
        for i, res in enumerate(results, 1):
            response += f"{i}. {res['content']}\n   Fuente: {res['source']}\n\n"
            
        return response
    except Exception as e:
        return f"Error al buscar en documentación: {str(e)}"

@tool
def check_system_health(config: RunnableConfig, component: str = "all") -> str:
    """
    Simula una verificación del estado del sistema.
    Puede revisar: 'database', 'api', 'auth' o 'all'.
    """
    # Simulación de estados (esto podría ser real conectando a endpoints de health)
    status_map = {
        "database": "ONLINE (Latency: 12ms)",
        "api": "ONLINE (Uptime: 99.9%)",
        "auth": "DEGRADED (High load detected)",
    }
    
    if component == "all":
        return "\n".join([f"- {k.upper()}: {v}" for k,v in status_map.items()])
    
    return f"- {component.upper()}: {status_map.get(component, 'UNKNOWN COMPONENT')}"
