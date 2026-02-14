import asyncio
import sys
import os

# Fix para Windows y Psycopg
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from langchain_core.messages import HumanMessage
from app.graph.workflow import workflow
from app.core.checkpoint import get_postgres_checkpointer

async def main():
    print("🧪 Verificando Ejecución Paralela y Nuevas Tools...")
    
    # Usuario pide algo que requiere dos agentes: "reparación" (Tech) y "presupuesto" (Billing/Sales)
    # Ajustamos el prompt para forzar paralelismo
    user_input = "Necesito agendar una reparación técnica para mi servidor y también quiero ver el catálogo de nuevos servidores para comprar uno si no tiene arreglo."
    print(f"👤 Usuario: {user_input}")
    
    try:
        async with get_postgres_checkpointer() as checkpointer:
            app = workflow.compile(checkpointer=checkpointer)
            
            config = {"configurable": {"thread_id": "test_parallel_1"}}
            
            print("⏳ Ejecutando grafo...")
            async for event in app.astream_events(
                {"messages": [HumanMessage(content=user_input)]},
                config,
                version="v1"
            ):
                kind = event["event"]
                if kind == "on_chain_start":
                    # Detectar ejecución paralela
                    if event["name"] in ["Tech", "Sales"]:
                        print(f"   🚀 [Event] Activando Agente: {event['name']}")
                    elif event["name"] == "Supervisor":
                         print(f"   👮 [Event] Supervisor pensando...")

            # Obtener estado final
            final_state = await app.aget_state(config)
            last_msg = final_state.values["messages"][-1]
            print(f"\n🤖 Respuesta Final: {last_msg.content}")
            
            print("\n✅ Verificación completada.")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
