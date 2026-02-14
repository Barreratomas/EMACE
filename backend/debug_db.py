from sqlmodel import Session, select
from app.core.database.session import engine
from app.core.database.models import Product

def check_1k2():
    with Session(engine) as session:
        product = session.exec(select(Product).where(Product.name == "1k2")).first()
        if product:
            print(f"DIAGNOSTIC: Producto '1k2' encontrado.")
            print(f"ID: {product.id}")
            print(f"Estado Actual: {product.status}")
            print(f"User ID: {product.user_id}")
        else:
            print("DIAGNOSTIC: Producto '1k2' no encontrado por nombre.")

if __name__ == "__main__":
    check_1k2()
