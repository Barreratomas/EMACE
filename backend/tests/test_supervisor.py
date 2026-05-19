import asyncio
import uuid
from langchain_core.messages import HumanMessage
from app.application.graph.workflow import workflow as graph
from app.infrastructure.adapters.checkpoint import get_postgres_checkpointer

async def main():
    print("🧪 INICIANDO TEST DE SUPERVISOR + TOOLS (Fase 4)...")
    
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    print(f"🧵 Thread ID generado: {thread_id}")
    
    # --- Interacción 1: Billing con Tools SQL ---
    print("\n🗣️ [Usuario]: 'Hola, soy juan.perez@email.com, ¿qué facturas tengo pendientes?'")
    async with get_postgres_checkpointer() as checkpointer:
        app = graph.compile(checkpointer=checkpointer)
        
        inputs = {"messages": [HumanMessage(content="Hola, soy juan.perez@email.com, ¿qué facturas tengo pendientes?")]}
        
        async for event in app.astream(inputs, config=config):
            for k, v in event.items():
                if k != "__end__":
                    print(f"   ➡️ Transición a nodo: {k}")
                    if "next" in v:
                        print(f"      Decisión Supervisor: {v['next']}")
                    if "messages" in v:
                        print(f"      Respuesta: {v['messages'][-1].content}")

    # --- Interacción 2: Sales con Tools ---
    print("\n🗣️ [Usuario]: '¿Tienen algún plan para empresas grandes?'")
    async with get_postgres_checkpointer() as checkpointer:
        app = graph.compile(checkpointer=checkpointer)
        
        inputs = {"messages": [HumanMessage(content="¿Tienen algún plan para empresas grandes?")]}
        
        async for event in app.astream(inputs, config=config):
            for k, v in event.items():
                if k != "__end__":
                    print(f"   ➡️ Transición a nodo: {k}")
                    if "next" in v:
                        print(f"      Decisión Supervisor: {v['next']}")
                    if "messages" in v:
                        print(f"      Respuesta: {v['messages'][-1].content}")

    # --- Interacción 3: Tech con Tools ---
    print("\n🗣️ [Usuario]: '¿Cómo está el estado del sistema de autenticación?'")
    async with get_postgres_checkpointer() as checkpointer:
        app = graph.compile(checkpointer=checkpointer)
        
        inputs = {"messages": [HumanMessage(content="¿Cómo está el estado del sistema de autenticación?")]}
        
        async for event in app.astream(inputs, config=config):
            for k, v in event.items():
                if k != "__end__":
                    print(f"   ➡️ Transición a nodo: {k}")
                    if "next" in v:
                        print(f"      Decisión Supervisor: {v['next']}")
                    if "messages" in v:
                        print(f"      Respuesta: {v['messages'][-1].content}")

if __name__ == "__main__":
    import sys
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
