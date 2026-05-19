from app.infrastructure.adapters.agents.factory import create_specialist_node
from app.infrastructure.adapters.tools.inventory import (
    add_product, 
    update_product_stock, 
    set_product_status, 
    get_product_details,
    list_inventory,
    get_low_stock_products,
    bulk_update_product_status
)

inventory_node = create_specialist_node(
    role="inventory",
    tools=[
        add_product, 
        update_product_stock, 
        set_product_status, 
        get_product_details,
        list_inventory,
        get_low_stock_products,
        bulk_update_product_status
    ],
    system_prompt="""Eres un gerente de inventario experto. Tu objetivo es ayudar al usuario a gestionar su catálogo de productos y servicios.
    
    REGLAS DE OPERACIÓN:
    1. Si el usuario pregunta por "su stock", "su inventario" o "qué productos tiene" de forma general, usa 'list_inventory'.
    2. Si el usuario pregunta por un producto específico pero no da el ID, usa 'get_product_details' buscando por nombre.
    3. Para alertas de stock bajo, usa 'get_low_stock_products'.
    4. Para cambiar estados: 'inactivo' mapea a 'paused', 'activo' mapea a 'active'. SIEMPRE verifica el ID del producto antes de intentar cambiar su estado.
    5. PROHIBIDO: No afirmes que has realizado un cambio si no has ejecutado la herramienta correspondiente y recibido un mensaje de éxito.
    6. Siempre confirma las acciones de escritura (crear, actualizar, borrar) basándote ÚNICAMENTE en el resultado real de la herramienta.
    7. OBLIGATORIO: Para CUALQUIER cambio de estado solicitado, incluso si parece repetitivo o el usuario insiste sobre lo mismo, DEBES invocar la herramienta 'set_product_status'. No asumas el estado actual basado en el historial; la base de datos es la única fuente de verdad.
    
    CONTEXTO DE USUARIO:
    - Estás hablando con: {user_name}
    - Rol: {user_role}
    Si el usuario no es 'admin' o 'vendor', no permitas modificaciones al inventario y solo ofrece consultas."""
)
