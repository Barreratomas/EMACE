from typing import List, Optional
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from sqlmodel import select
from app.core.database.session import get_session
from app.core.database.models import Invoice, User, Customer

@tool
def get_client_invoices(email: str, config: RunnableConfig) -> str:
    """
    Busca todas las facturas asociadas a un cliente dado su email.
    Retorna una lista de facturas con ID, monto, estado y fecha.
    """
    user_id = config.get("configurable", {}).get("user_id")
    if not user_id:
        return "Error de Seguridad: No se identificó al usuario (Vendor)."

    session_gen = get_session()
    session = next(session_gen)
    try:
        # Buscar clientes (Filtrado por Vendedor actual)
        statement = select(Customer).where(Customer.email == email, Customer.user_id == user_id)
        customers = session.exec(statement).all()
        
        if not customers:
            return f"No se encontró ningún cliente con el email: {email} asociado a tu cuenta."
            
        # Buscar facturas de todos los clientes encontrados (debería ser 1 normalmente)
        all_invoices = []
        customer_names = set()
        for cust in customers:
            customer_names.add(cust.name)
            invs = session.exec(select(Invoice).where(Invoice.customer_id == cust.id)).all()
            all_invoices.extend(invs)
        
        if not all_invoices:
            names_str = ", ".join(customer_names)
            return f"El cliente {names_str} ({email}) no tiene facturas registradas."
            
        result = f"Facturas encontradas para {email} ({len(customers)} perfiles encontrados):\n"
        for inv in all_invoices:
            result += f"- ID: {inv.id} | Monto: ${inv.amount} | Estado: {inv.status} | Vence: {inv.due_date}\n"
            
        return result
    finally:
        session.close()

@tool
def check_invoice_status(invoice_id: int, config: RunnableConfig) -> str:
    """
    Verifica el estado detallado de una factura específica por su ID.
    """
    user_id = config.get("configurable", {}).get("user_id")
    if not user_id:
        return "Error de Seguridad: No se identificó al usuario."

    session_gen = get_session()
    session = next(session_gen)
    try:
        # Join con Customer para verificar user_id
        statement = select(Invoice, Customer).join(Customer).where(
            Invoice.id == invoice_id,
            Customer.user_id == user_id
        )
        result = session.exec(statement).first()
        
        if not result:
            return f"No se encontró ninguna factura con ID {invoice_id} o no pertenece a tus clientes."
            
        invoice, customer = result
        return f"Factura #{invoice.id} (Cliente: {customer.name}): Estado '{invoice.status}'. Monto: ${invoice.amount}. Fecha de emisión: {invoice.issued_at}."
    finally:
        session.close()

@tool
def check_my_invoices(config: RunnableConfig) -> str:
    """
    Permite que un cliente consulte sus propias facturas.
    Esta herramienta identifica automáticamente al cliente por su sesión.
    """
    customer_id = config.get("configurable", {}).get("customer_id")
    if not customer_id:
        return "Error: No se pudo identificar tu perfil de cliente. Por favor contacta con soporte."

    session_gen = get_session()
    session = next(session_gen)
    try:
        statement = select(Invoice).where(Invoice.customer_id == customer_id)
        invoices = session.exec(statement).all()
        
        if not invoices:
            return "No tienes facturas registradas en nuestro sistema actualmente."
            
        result = "Tus facturas registradas:\n"
        for inv in invoices:
            result += f"- Factura #{inv.id} | Monto: ${inv.amount} | Estado: {inv.status} | Fecha: {inv.issued_at.date()}\n"
            
        return result
    finally:
        session.close()
