import sys
import os
import asyncio
from langchain_core.runnables import RunnableConfig

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.tools.inventory import add_product, set_product_status
from app.tools.sales import search_product_catalog
from app.core.database.session import engine
from app.core.database.models import User, Product
from sqlmodel import Session, select

async def test_tool_context():
    print("--- 🔐 Testing Auth Context in Tools ---")
    
    # 1. Setup Users
    with Session(engine) as session:
        users = session.exec(select(User)).all()
        if len(users) < 2:
            print("❌ Need at least 2 users. Run seed_data.py first.")
            return
            
        u1 = users[0]
        u2 = users[1]
        
        # Detach/Copy IDs to use outside session
        u1_id = u1.id
        u2_id = u2.id
        
        print(f"User 1: {u1_id} ({u1.name})")
        print(f"User 2: {u2_id} ({u2.name})")

        # Clean previous test data
        existing = session.exec(select(Product).where(Product.name == "AuthTestProduct")).all()
        for p in existing:
            session.delete(p)
        session.commit()

    # 2. Test Add Product with User 1
    config_u1 = RunnableConfig(configurable={"user_id": u1_id})
    print("\n[User 1] Adding product 'AuthTestProduct'...")
    res = add_product.invoke(
        {"name": "AuthTestProduct", "category": "Test", "price": 10.0, "description": "Test Desc"},
        config=config_u1
    )
    print(res)
    
    if "creado exitosamente" not in res:
        print("❌ Failed to create product for User 1")
        return

    # 3. Test Search with User 2 (Should NOT see it)
    config_u2 = RunnableConfig(configurable={"user_id": u2_id})
    print("\n[User 2] Searching 'AuthTestProduct'...")
    res_search = search_product_catalog.invoke(
        {"query": "AuthTestProduct"},
        config=config_u2
    )
    print(res_search)
    
    if "No encontré productos" in res_search:
        print("✅ User 2 correctly CANNOT see User 1's product.")
    else:
        print("❌ User 2 SAW User 1's product!")

    # 4. Test Search with User 1 (Should see it)
    print("\n[User 1] Searching 'AuthTestProduct'...")
    res_search_u1 = search_product_catalog.invoke(
        {"query": "AuthTestProduct"},
        config=config_u1
    )
    print(res_search_u1)
    
    if "AuthTestProduct" in res_search_u1:
        print("✅ User 1 sees their own product.")
    else:
        print("❌ User 1 CANNOT see their own product!")

    # 5. Test Modify with User 2 (Should fail)
    print("\n[User 2] Trying to archive User 1's product...")
    # Get ID first
    with Session(engine) as session:
        prod = session.exec(select(Product).where(Product.name == "AuthTestProduct")).first()
        prod_id = prod.id if prod else 99999
        
    res_mod = set_product_status.invoke(
        {"product_id": prod_id, "status": "archived"},
        config=config_u2
    )
    print(res_mod)
    
    if "no te pertenece" in res_mod or "no encontrado" in res_mod:
        print("✅ User 2 blocked from modifying User 1's product.")
    else:
        print("❌ User 2 WAS ABLE to modify User 1's product!")

if __name__ == "__main__":
    asyncio.run(test_tool_context())
