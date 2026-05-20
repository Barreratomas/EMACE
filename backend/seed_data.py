import os
import json
import csv
import sys
from datetime import datetime, timezone
from sqlmodel import Session, select
from app.infrastructure.database.session import engine
from app.domain.models.auth import User, Role
from app.domain.models.inventory import Product
from app.domain.models.customer import Customer
from app.domain.models.billing import Invoice, VendorAccessState
from app.domain.models.support import Ticket, Appointment
from app.infrastructure.security import get_password_hash

# Intentar importar el servicio de ingesta para RAG (opcional si falla)
try:
    from app.infrastructure.adapters.rag import ingestion as ingestion_service
except ImportError:
    ingestion_service = None

# --- Helpers de Carga SQL ---

def seed_roles():
    print("📥 Cargando Roles predefinidos...")
    with Session(engine) as session:
        roles = [
            {"name": "admin", "description": "Administrador total del sistema", "permissions": ["*:*"]},
            {"name": "vendor", "description": "Dueño de tienda / Vendor", "permissions": ["products:*", "customers:*", "invoices:*", "appointments:*", "knowledge:*", "agents:*"]},
            {"name": "seller", "description": "Vendedor con acceso limitado", "permissions": ["products:read", "customers:read", "invoices:read"]},
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
    print(f"📥 Cargando Usuarios (Vendors e IAM) desde {file_path}...")
    with Session(engine) as session:
        roles = {r.name: r for r in session.exec(select(Role)).all()}
        count = 0
        if not os.path.exists(file_path):
            print(f"⚠️ No se encontró {file_path}")
            return

        with open(file_path, mode='r', encoding='utf-8') as f:
            rows = list(csv.DictReader(f))
            
            # Pasada 1: Vendors (Dueños de tienda)
            for row in [r for r in rows if not r.get('parent_email')]:
                existing = session.exec(select(User).where(User.email == row['email'])).first()
                if not existing:
                    role_name = row.get('role', 'admin')
                    role = roles.get(role_name)
                    user = User(
                        name=row['name'],
                        email=row['email'],
                        plan_type=row.get('plan_type', 'basic'),
                        role_id=role.id if role else None,
                        password_hash=get_password_hash(row.get('password', 'Default123!@#'))
                    )
                    session.add(user)
                    count += 1
            session.commit()

            # Pasada 2: Usuarios IAM (Hijos)
            for row in [r for r in rows if r.get('parent_email')]:
                existing = session.exec(select(User).where(User.email == row['email'])).first()
                if not existing:
                    parent = session.exec(select(User).where(User.email == row['parent_email'])).first()
                    if not parent:
                        continue
                    role_name = row.get('role', 'seller')
                    role = roles.get(role_name)
                    user = User(
                        name=row['name'],
                        email=row['email'],
                        plan_type=parent.plan_type,
                        role_id=role.id if role else None,
                        parent_id=parent.id,
                        password_hash=get_password_hash(row.get('password', 'Default123!@#'))
                    )
                    session.add(user)
                    count += 1
            session.commit()
        print(f"✅ {count} usuarios procesados.")

def seed_billing():
    print("📥 Inicializando estados de Billing (Multi-tenant)...")
    with Session(engine) as session:
        vendors = session.exec(select(User).where(User.parent_id == None)).all()
        count = 0
        for v in vendors:
            existing = session.exec(select(VendorAccessState).where(VendorAccessState.vendor_id == v.id)).first()
            if not existing:
                state = VendorAccessState(
                    vendor_id=v.id,
                    access_mode="subscription",
                    source="trial",
                    valid_until=datetime.now(timezone.utc).replace(tzinfo=None)
                )
                session.add(state)
                count += 1
        session.commit()
        print(f"✅ {count} estados de acceso creados.")

def seed_customers(file_path: str):
    print(f"📥 Cargando Clientes (Customers) desde {file_path}...")
    with Session(engine) as session:
        count = 0
        if not os.path.exists(file_path):
            print(f"⚠️ No se encontró {file_path}")
            return
            
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                vendor = session.exec(select(User).where(User.email == row['vendor_email'])).first()
                if not vendor:
                    continue
                
                existing = session.exec(select(Customer).where(
                    Customer.email == row['email'], 
                    Customer.user_id == vendor.id
                )).first()
                
                if not existing:
                    customer = Customer(
                        user_id=vendor.id,
                        name=row['name'],
                        email=row['email'],
                        phone=row.get('phone')
                    )
                    session.add(customer)
                    count += 1
        session.commit()
        print(f"✅ {count} clientes insertados.")

def seed_products(file_path: str):
    print(f"📥 Cargando Productos (Inventory) desde {file_path}...")
    with Session(engine) as session:
        count = 0
        if not os.path.exists(file_path):
            print(f"⚠️ No se encontró {file_path}")
            return
            
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                vendor = session.exec(select(User).where(User.email == row['vendor_email'])).first()
                if not vendor:
                    continue
                    
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
                        stock=int(row.get('stock', 0)),
                        description=row['description'],
                        type=row.get('type', 'physical'),
                        status=row.get('status', 'active'),
                        min_stock_threshold=int(row.get('min_stock_threshold', 5))
                    )
                    session.add(product)
                    count += 1
        session.commit()
        print(f"✅ {count} productos insertados.")

def seed_invoices(file_path: str):
    print(f"📥 Cargando Facturas (Billing) desde {file_path}...")
    with Session(engine) as session:
        count = 0
        if not os.path.exists(file_path):
            print(f"⚠️ No se encontró {file_path}")
            return
            
        with open(file_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                vendor = session.exec(select(User).where(User.email == row['vendor_email'])).first()
                if not vendor: continue
                
                customer = session.exec(select(Customer).where(
                    Customer.email == row['customer_email'],
                    Customer.user_id == vendor.id
                )).first()
                
                if not customer: continue

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
        print(f"✅ {count} facturas insertadas.")

def seed_support(tickets_path: str, appointments_path: str):
    print(f"📥 Cargando Tickets y Citas (Support) desde {tickets_path} y {appointments_path}...")
    with Session(engine) as session:
        # Seed Tickets
        ticket_count = 0
        if os.path.exists(tickets_path):
            with open(tickets_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    vendor = session.exec(select(User).where(User.email == row['vendor_email'])).first()
                    customer = session.exec(select(Customer).where(Customer.email == row['customer_email'], Customer.user_id == (vendor.id if vendor else None))).first()
                    if vendor and customer:
                        ticket = Ticket(
                            user_id=vendor.id,
                            customer_id=customer.id,
                            subject=row['subject'],
                            description=row['description'],
                            priority=row['priority'],
                            status=row['status']
                        )
                        session.add(ticket)
                        ticket_count += 1
        
        # Seed Appointments
        appo_count = 0
        if os.path.exists(appointments_path):
            with open(appointments_path, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    vendor = session.exec(select(User).where(User.email == row['vendor_email'])).first()
                    customer = session.exec(select(Customer).where(Customer.email == row['customer_email'], Customer.user_id == (vendor.id if vendor else None))).first()
                    if vendor and customer:
                        appointment = Appointment(
                            user_id=vendor.id,
                            customer_id=customer.id,
                            agent_role=row['agent_role'],
                            datetime_slot=datetime.strptime(row['datetime_slot'], "%Y-%m-%d %H:%M:%S"),
                            status=row['status']
                        )
                        session.add(appointment)
                        appo_count += 1
        
        session.commit()
        print(f"✅ {ticket_count} tickets y {appo_count} citas insertados.")

def ingest_documents(directory: str):
    if not ingestion_service:
        print("⚠️ Servicio de ingesta no disponible.")
        return
        
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
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    seed_dir = "seeds"
    
    if mode in ["all", "sql"]:
        print("--- 🛠️ Iniciando Carga SQL Multi-tenant ---")
        seed_roles()
        seed_users(os.path.join(seed_dir, "users.csv"))
        seed_billing()
        seed_customers(os.path.join(seed_dir, "customers.csv"))
        seed_products(os.path.join(seed_dir, "products.csv"))
        seed_invoices(os.path.join(seed_dir, "invoices.csv"))
        seed_support(
            os.path.join(seed_dir, "tickets.csv"),
            os.path.join(seed_dir, "appointments.csv")
        )

    if mode in ["all", "vector"]:
        print("\n--- 🧠 Iniciando Carga Vectorial ---")
        ingest_documents(seed_dir)

if __name__ == "__main__":
    main()
