from app.infrastructure.adapters.agents.factory import create_specialist_node
from app.infrastructure.adapters.tools.sales import (
    search_product_catalog, 
    check_stock, 
    create_order,
    add_to_cart,
    view_cart,
    checkout_cart
)
from app.infrastructure.adapters.tools.calendar import check_calendar_availability, schedule_appointment
from app.infrastructure.adapters.tools.billing import check_my_invoices
from app.domain.prompts import CUSTOMER_SUPPORT_SYSTEM_PROMPT

# Nodo estándar para Vendedores (Internal Sales)
sales_node = create_specialist_node(
    role="sales",
    tools=[search_product_catalog, check_stock, check_calendar_availability, schedule_appointment],
    system_prompt="""Eres un vendedor consultivo. Busca productos y stock. Agenda demos o reuniones comerciales.
    
    CONTEXTO DE USUARIO:
    - Cliente: {user_name}
    - Rol: {user_role}"""
)

# Nodo optimizado para Clientes Finales (Customer Support)
customer_support_node = create_specialist_node(
    role="customer_support",
    tools=[
        search_product_catalog, 
        check_stock, 
        check_calendar_availability, 
        schedule_appointment, 
        check_my_invoices, 
        create_order,
        add_to_cart,
        view_cart,
        checkout_cart
    ],
    system_prompt=CUSTOMER_SUPPORT_SYSTEM_PROMPT
)
