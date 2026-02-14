import os
import json
import csv
import sys
from sqlmodel import Session, select
from app.core.database.session import engine
from app.core.database.models import User, Product, Appointment, Invoice, Ticket, Customer, Role

# --- Helpers de Carga SQL ---

def seed_roles():
    print("📥 Cargando Roles predefinidos...")
    with Session(engine) as session:
        roles = [
            {"name": "admin", "description": "Administrador total del sistema", "permissions": ["*:*"]},
            {"name": "seller", "description": "Vendedor con acceso a sus productos y clientes", "permissions": ["products:*", "customers:*", "invoices:*", "appointments:*"]},
        ]
        count = 0
        for r_data in roles:
            existing = session.exec(select(Role).where(Role.name == r_data["name"])).first()
            if not existing:
                role = Role(**r_data)
                session.add(role)
                count += 1
        session.commit()
        print(f"✅ {count} roles insertados.")

def seed_users(file_path: str):
    print(f"📥 Cargando Usuarios (Vendedores) desde {file_path}...")
    with Session(engine) as session:
        # Obtener el rol de admin por defecto
        admin_role = session.exec(select(Role).where(Role.name == "admin")).first()
        
        count = 0
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Verificar si existe
                existing = session.exec(select(User).where(User.email == row['email'])).first()
                if not existing:
                    user = User(
                        name=row['name'],
                        email=row['email'],
                        plan_type=row.get('plan_type', 'basic'),
                        role_id=admin_role.id if admin_role else None,
                        password_hash="argon2_placeholder" # Placeholder para 9.2
                    )
                    session.add(user)
                    count += 1
        session.commit()
        print(f"✅ {count} usuarios (vendedores) insertados.")

def seed_customers():
    print(f"📥 Generando Clientes (Customers) de prueba...")
    with Session(engine) as session:
        vendors = session.exec(select(User)).all()
        if not vendors:
            print("⚠️ No hay vendedores (Users) para asignar clientes.")
            return

        count = 0
        for vendor in vendors:
            # Crear un cliente de prueba para cada vendedor
            cust_email = f"cliente_{vendor.id}@test.com"
            existing = session.exec(select(Customer).where(Customer.email == cust_email)).first()
            if not existing:
                customer = Customer(
                    user_id=vendor.id,
                    name=f"Cliente de {vendor.name}",
                    email=cust_email,
                    phone="555-0000"
                )
                session.add(customer)
                count += 1
        
        session.commit()
        print(f"✅ {count} clientes insertados.")

def seed_products(file_path: str):
    print(f"📥 Cargando Productos desde {file_path}...")
    with Session(engine) as session:
        # Asignar productos al primer vendedor por defecto
        vendor = session.exec(select(User)).first()
        if not vendor:
            print("⚠️ No hay vendedores para asignar productos.")
            return
            
        count = 0
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Handle optional fields
                stock_val = row.get('stock', '0')
                stock = int(stock_val) if stock_val and stock_val.strip() else 0
                
                min_stock_val = row.get('min_stock_threshold', '')
                min_stock = int(min_stock_val) if min_stock_val and min_stock_val.strip() else None

                # Check duplicates by name AND user_id
                existing = session.exec(select(Product).where(
                    Product.name == row['name'], 
                    Product.user_id == vendor.id
                )).first()

                if not existing:
                    product = Product(
                        user_id=vendor.id,
                        name=row['name'],
                        category=row['category'],
                        price=float(row['price']),
                        stock=stock,
                        description=row['description'],
                        type=row.get('type', 'physical'),
                        status=row.get('status', 'active'),
                        min_stock_threshold=min_stock,
                        sla=row.get('sla')
                    )
                    session.add(product)
                    count += 1
        session.commit()
        print(f"✅ {count} productos insertados para el vendedor {vendor.name}.")

def seed_invoices(file_path: str):
    print(f"📥 Cargando Facturas desde {file_path}...")
    with Session(engine) as session:
        count = 0
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # El CSV original tenia 'client_email'.
                # Ahora debemos buscar un Customer con ese email, O crear una factura para un cliente de prueba.
                # Para simplificar la migración, asignaremos las facturas al primer cliente del primer vendedor.
                
                vendor = session.exec(select(User)).first()
                if not vendor: break
                
                customer = session.exec(select(Customer).where(Customer.user_id == vendor.id)).first()
                if not customer: 
                    print("⚠️ No hay clientes para asignar facturas.")
                    break

                from datetime import datetime
                # Check for duplicates? Assuming file is append-only or clean
                invoice = Invoice(
                    user_id=vendor.id,
                    customer_id=customer.id,
                    amount=float(row['amount']),
                    status=row['status'],
                    due_date=datetime.strptime(row['due_date'], "%Y-%m-%d")
                )
                session.add(invoice)
                count += 1
        session.commit()
        print(f"✅ {count} facturas insertadas (asignadas a {customer.name}).")

# --- Helpers de Carga Vectorial ---

def ingest_documents(directory: str):
    print(f"📚 Ingestando documentos desde {directory}...")
    supported_exts = [".pdf", ".md", ".txt"]
    count = 0
    for root, _, files in os.walk(directory):
        for file in files:
            ext = os.path.splitext(file)[1]
            if ext in supported_exts:
                full_path = os.path.join(root, file)
                try:
                    ingestion_service.ingest_file(full_path)
                    count += 1
                except Exception as e:
                    print(f"❌ Error en {file}: {e}")
    print(f"✅ {count} documentos procesados.")

# --- Main CLI ---

def main():
    if len(sys.argv) < 2:
        print("Uso: python seed_data.py [all|sql|vector]")
        print("Coloca tus archivos en 'data/inputs/'")
        print("Archivos esperados: users.csv, products.csv, invoices.csv y documentos (.pdf/.md)")
        return

    mode = sys.argv[1]
    input_dir = "data/inputs"
    
    # Rutas esperadas
    users_csv = os.path.join(input_dir, "users.csv")
    products_csv = os.path.join(input_dir, "products.csv")
    invoices_csv = os.path.join(input_dir, "invoices.csv")
    
    if mode in ["all", "sql"]:
        print("--- 🛠️ Iniciando Carga SQL ---")
        seed_roles() # Cargar roles antes que usuarios
        if os.path.exists(users_csv): 
            seed_users(users_csv)
            seed_customers() # Generar clientes automaticos para los vendedores
        else: print(f"ℹ️ No se encontró {users_csv}, saltando usuarios.")
        
        if os.path.exists(products_csv): seed_products(products_csv)
        else: print(f"ℹ️ No se encontró {products_csv}, saltando productos.")

        if os.path.exists(invoices_csv): seed_invoices(invoices_csv)
        else: print(f"ℹ️ No se encontró {invoices_csv}, saltando facturas.")

    if mode in ["all", "vector"]:
        print("\n--- 🧠 Iniciando Carga Vectorial ---")
        ingest_documents(input_dir)

if __name__ == "__main__":
    main()
