import asyncio
import os
from sqlmodel import Session, select
from app.core.database.session import engine, get_async_session
from app.core.database.models import User, Product
from app.repositories.product import product_repo
from app.core.memory.episodic import episodic_memory
from app.core.rag.retriever import retriever
import uuid

# --- Helpers ---

def get_or_create_users(session):
    u1 = session.exec(select(User).where(User.email == "vendor1@test.com")).first()
    u2 = session.exec(select(User).where(User.email == "vendor2@test.com")).first()
    
    if not u1:
        u1 = User(name="Vendor One", email="vendor1@test.com", plan_type="premium")
        session.add(u1)
    if not u2:
        u2 = User(name="Vendor Two", email="vendor2@test.com", plan_type="basic")
        session.add(u2)
    session.commit()
    session.refresh(u1)
    session.refresh(u2)
    return u1, u2

def setup_data(session, u1, u2):
    # Limpiar productos de prueba previos
    session.exec(select(Product)).all() # No delete all to avoid breaking other tests, just add distinctive ones

    # Producto Vendedor 1
    p1 = Product(user_id=u1.id, name="Producto V1 Exclusive", category="Test", price=100.0, description="Solo para V1")
    session.add(p1)
    
    # Producto Vendedor 2
    p2 = Product(user_id=u2.id, name="Producto V2 Exclusive", category="Test", price=200.0, description="Solo para V2")
    session.add(p2)
    
    session.commit()
    return p1, p2

async def verify_sql_isolation(u1, u2):
    print("\n--- 🔒 Verificando Aislamiento SQL ---")
    async for session in get_async_session():
        # Vendedor 1 debería ver SU producto
        prods_v1 = await product_repo.get_all_async(session, user_id=u1.id, type="physical")
        names_v1 = [p.name for p in prods_v1 if "Exclusive" in p.name]
        print(f"Vendor 1 ve: {names_v1}")
        
        # Vendedor 2 debería ver SU producto
        prods_v2 = await product_repo.get_all_async(session, user_id=u2.id, type="physical")
        names_v2 = [p.name for p in prods_v2 if "Exclusive" in p.name]
        print(f"Vendor 2 ve: {names_v2}")
        
        if "Producto V2 Exclusive" in names_v1:
            print("❌ FALLO: Vendor 1 vio producto de Vendor 2!")
        elif "Producto V1 Exclusive" in names_v2:
            print("❌ FALLO: Vendor 2 vio producto de Vendor 1!")
        else:
            print("✅ Aislamiento SQL Correcto.")
        break

def verify_vector_isolation(u1, u2):
    print("\n--- 🧠 Verificando Aislamiento Vectorial ---")
    
    # Inyectar memorias
    mem1 = f"Secreto de V1: {uuid.uuid4()}"
    mem2 = f"Secreto de V2: {uuid.uuid4()}"
    
    print(f"Inyectando memoria V1: {mem1}")
    episodic_memory.remember_interaction("Guardar secreto V1", mem1, user_id=u1.id)
    
    print(f"Inyectando memoria V2: {mem2}")
    episodic_memory.remember_interaction("Guardar secreto V2", mem2, user_id=u2.id)
    
    # Intentar recuperar cruzado
    print("Intento de V1 de leer secretos...")
    results_v1 = episodic_memory.recall_similar_interactions("Secreto", user_id=u1.id)
    
    if mem2 in results_v1:
        print("❌ FALLO: V1 pudo leer memoria de V2")
    elif mem1 not in results_v1:
        print("⚠️ ALERTA: V1 no encontró su propia memoria (puede ser por delay de indexación)")
    else:
        print("✅ V1 solo vio sus datos.")

    print("Intento de V2 de leer secretos...")
    results_v2 = episodic_memory.recall_similar_interactions("Secreto", user_id=u2.id)
    
    if mem1 in results_v2:
        print("❌ FALLO: V2 pudo leer memoria de V1")
    else:
        print("✅ V2 solo vio sus datos.")

async def main():
    with Session(engine) as session:
        u1, u2 = get_or_create_users(session)
        setup_data(session, u1, u2)
        
        await verify_sql_isolation(u1, u2)
        verify_vector_isolation(u1, u2)

if __name__ == "__main__":
    asyncio.run(main())
