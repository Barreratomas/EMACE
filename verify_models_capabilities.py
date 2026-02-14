import asyncio
from langchain_core.messages import HumanMessage
from app.core.llm import get_llm

async def verify_model(role: str):
    print(f"\n--- Verificando Rol: {role.upper()} ---")
    try:
        llm = get_llm(role=role, temperature=0.7)
        print(f"Modelo asignado: {llm.model_name}")
        
        # Pregunta simple para verificar generación de texto
        msg = HumanMessage(content="Responde brevemente: ¿Quién eres y cuál es tu función principal?")
        
        # Usamos ainvoke para no bloquear si hay timeouts (aunque aquí es secuencial)
        response = await llm.ainvoke([msg])
        
        print(f"✅ Respuesta recibida ({len(response.content)} chars):")
        print(f"   \"{response.content[:100]}...\"") # Mostrar primeros 100 chars
        return True
    except Exception as e:
        print(f"❌ ERROR con rol {role}: {e}")
        return False

async def main():
    roles = ["supervisor", "billing", "tech", "sales", "qa", "rag"]
    results = {}
    
    print("🚀 Iniciando verificación de capacidades de modelos por rol...")
    
    for role in roles:
        success = await verify_model(role)
        results[role] = success
        
    print("\n--- RESUMEN FINAL ---")
    all_ok = True
    for role, status in results.items():
        mark = "✅ OK" if status else "❌ FALLÓ"
        if not status: all_ok = False
        print(f"{role.ljust(15)}: {mark}")
        
    if all_ok:
        print("\n🎉 Todos los modelos respondieron correctamente a prompts básicos.")
    else:
        print("\n⚠️ Algunos modelos fallaron. Revisa los logs.")

if __name__ == "__main__":
    # Fix para Windows Event Loop Policy si es necesario, pero corremos directo
    asyncio.run(main())
