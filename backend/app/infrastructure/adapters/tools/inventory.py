from typing import Literal
from slowapi import Limiter
from typing import Optional, Annotated, List
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from sqlmodel import Session, select
from app.infrastructure.database.session import engine
from app.domain.models import Product, User

@tool
def add_product(
    name: str, 
    category: str, 
    price: float, 
    description: str, 
    config: RunnableConfig,
    type: str = "physical", 
    stock: int = 0, 
    sla: Optional[str] = None
) -> str:
    """
    Agrega un nuevo producto al catálogo.
    Args:
        name: Nombre del producto.
        category: Categoría (ej: Hardware, Software, Consultoría).
        price: Precio unitario.
        description: Descripción detallada.
        type: 'physical' o 'service'.
        stock: Cantidad inicial (solo físicos).
        sla: Acuerdo de nivel de servicio (solo servicios, ej: '24h').
    """
    raw_user_id = config.get("configurable", {}).get("user_id")
    if not raw_user_id:
        return "Error de Seguridad: No se identificó al usuario (Vendor) en el contexto."
    try:
        user_id = int(raw_user_id)
    except (TypeError, ValueError):
        return "Error de Seguridad: Identificador de usuario inválido."

    with Session(engine) as session:
        existing = session.exec(select(Product).where(Product.name == name, Product.user_id == user_id)).first()
        if existing:
            return f"Error: El producto '{name}' ya existe en tu catálogo (ID: {existing.id})."
        
        new_product = Product(
            user_id=user_id,
            name=name,
            category=category,
            price=price,
            description=description,
            type=type,
            stock=stock if type == 'physical' else None,
            sla=sla if type == 'service' else None,
            status="active"
        )
        session.add(new_product)
        session.commit()
        session.refresh(new_product)
        return f"Producto creado exitosamente: {new_product.name} (ID: {new_product.id}, Tipo: {new_product.type})."

@tool
def update_product_stock(
    product_id: int, 
    quantity_delta: int,
    config: RunnableConfig
) -> str:
    """
    Ajusta el stock de un producto físico.
    Args:
        product_id: ID del producto.
        quantity_delta: Cantidad a sumar (positivo) o restar (negativo).
    """
    raw_user_id = config.get("configurable", {}).get("user_id")
    if not raw_user_id:
        return "Error de Seguridad: No se identificó al usuario."
    try:
        user_id = int(raw_user_id)
    except (TypeError, ValueError):
        return "Error de Seguridad: Identificador de usuario inválido."

    with Session(engine) as session:
        product = session.exec(select(Product).where(Product.id == product_id, Product.user_id == user_id)).first()
        if not product:
            return f"Error: Producto ID {product_id} no encontrado o no te pertenece."
        
        if product.type != 'physical':
            return f"Error: No se puede gestionar stock para servicios ('{product.name}')."
            
        current_stock = product.stock or 0
        new_stock = current_stock + quantity_delta
        
        if new_stock < 0:
            return f"Error: Stock insuficiente. Stock actual: {current_stock}, Intentado restar: {abs(quantity_delta)}."
            
        product.stock = new_stock
        
        session.add(product)
        session.commit()
        session.refresh(product)
        
        alert = ""
        if product.min_stock_threshold and new_stock < product.min_stock_threshold:
            alert = f" ALERTA: Stock bajo (Mínimo: {product.min_stock_threshold})."
            
        return f"Stock actualizado para '{product.name}'. Nuevo stock: {new_stock}.{alert}"

@tool
def set_product_status(
    product_id: int, 
    status: Literal["active", "paused", "archived"],
    config: RunnableConfig
) -> str:
    """
    Cambia el estado de un producto (active, paused, archived).
    Args:
        status: 'active' (activo/visible), 'paused' (inactivo/pausado), 'archived' (archivado/borrado).
    """
    raw_user_id = config.get("configurable", {}).get("user_id")
    if not raw_user_id:
        return "Error de Seguridad: No se identificó al usuario."
    try:
        user_id = int(raw_user_id)
    except (TypeError, ValueError):
        return "Error de Seguridad: Identificador de usuario inválido."

    print(f"DEBUG TOOL [set_product_status]: Recibido status='{status}'")
    
    with Session(engine) as session:
        # Forzar que la sesión no use cache y vea datos frescos
        session.expire_all()
        
        product = session.exec(select(Product).where(Product.id == product_id, Product.user_id == user_id)).first()
        if not product:
            error_msg = f"Error: Producto ID {product_id} no encontrado o no te pertenece."
            print(f"DEBUG TOOL [set_product_status]: {error_msg}")
            return error_msg
            
        old_status = product.status
        print(f"DEBUG TOOL [set_product_status]: Producto '{product.name}' (ID: {product_id}) encontrado. Estado actual en DB: '{old_status}', Objetivo: '{status}'")
                
        if old_status == status:
            info_msg = f"Información: El producto '{product.name}' (ID: {product_id}) ya se encuentra en estado '{status}' (actual: {old_status})."
            print(f"DEBUG TOOL [set_product_status]: {info_msg}")
            return info_msg

        # Actualización explícita
        print(f"DEBUG TOOL [set_product_status]: Intentando commit: {old_status} -> {status}")
        product.status = status
        session.add(product)
        session.commit()
        
        # Forzar recarga física desde la DB
        session.refresh(product)
        print(f"DEBUG TOOL [set_product_status]: Post-commit refresh: El estado real en DB es '{product.status}'")
        
        # Verificación post-commit
        if product.status == status:
            success_msg = f"Estado de '{product.name}' (ID: {product.id}) actualizado exitosamente: {old_status} -> {product.status}."
            print(f"DEBUG TOOL [set_product_status]: SUCCESS: {success_msg}")
            return success_msg
        else:
            error_msg = f"Error Crítico: No se pudo confirmar la actualización en la base de datos. Estado actual sigue siendo: {product.status}."
            print(f"DEBUG TOOL [set_product_status]: CRITICAL ERROR: {error_msg}")
            return error_msg

@tool
def get_product_details(product_name_or_id: str, config: RunnableConfig) -> str:
    """
    Obtiene detalles completos de un producto para gestión.
    Puede buscar por ID (si es numérico) o por nombre.
    """
    raw_user_id = config.get("configurable", {}).get("user_id")
    if not raw_user_id:
        return "Error de Seguridad: No se identificó al usuario."
    try:
        user_id = int(raw_user_id)
    except (TypeError, ValueError):
        return "Error de Seguridad: Identificador de usuario inválido."

    with Session(engine) as session:
        if product_name_or_id.isdigit():
            product = session.exec(select(Product).where(Product.id == int(product_name_or_id), Product.user_id == user_id)).first()
        else:
            product = session.exec(select(Product).where(Product.name.ilike(f"%{product_name_or_id}%"), Product.user_id == user_id)).first()
            
        if not product:
            return "Producto no encontrado o no te pertenece."
            
        return f"""
        ID: {product.id}
        Nombre: {product.name}
        Tipo: {product.type}
        Precio: ${product.price}
        Estado: {product.status}
        Stock: {product.stock if product.type == 'physical' else 'N/A'}
        SLA: {product.sla if product.type == 'service' else 'N/A'}
        Descripción: {product.description}
        """

@tool
def list_inventory(config: RunnableConfig) -> str:
    """
    Obtiene una lista resumida de todos los productos en el inventario del usuario con su stock actual.
    Útil para responder preguntas como "¿qué stock tengo?", "¿cuáles son mis productos?" o "dame un resumen de mi inventario".
    """
    raw_user_id = config.get("configurable", {}).get("user_id")
    if not raw_user_id:
        return "Error de Seguridad: No se identificó al usuario."
    try:
        user_id = int(raw_user_id)
    except (TypeError, ValueError):
        return "Error de Seguridad: Identificador de usuario inválido."

    with Session(engine) as session:
        products = session.exec(
            select(Product).where(
                Product.user_id == user_id,
                Product.status != "archived"
            )
        ).all()
        
        if not products:
            return "No tienes productos registrados en tu inventario."
            
        result = "### Resumen de Inventario:\n"
        for p in products:
            stock_info = f"Stock: {p.stock}" if p.type == "physical" else f"SLA: {p.sla}"
            result += f"- **{p.name}** (ID: {p.id}) | Categoría: {p.category} | Precio: ${p.price} | {stock_info} | Estado: {p.status}\n"
            
        return result

@tool
def get_low_stock_products(config: RunnableConfig) -> str:
    """
    Obtiene productos con stock bajo (por debajo del umbral configurado).
    """
    raw_user_id = config.get("configurable", {}).get("user_id")
    if not raw_user_id:
        return "Error de Seguridad: No se identificó al usuario."
    try:
        user_id = int(raw_user_id)
    except (TypeError, ValueError):
        return "Error de Seguridad: Identificador de usuario inválido."

    from app.infrastructure.repositories.product import product_repo
    
    with Session(engine) as session:
        low_stock_products = product_repo.check_low_stock(session, user_id)
        
        if not low_stock_products:
            return "No hay productos con stock bajo."
            
        result = "Productos con stock bajo:\n"
        for product in low_stock_products:
            result += f"- {product.name} (ID: {product.id}): Stock actual {product.stock}, Umbral: {product.min_stock_threshold}\n"
            
        return result

@tool
def bulk_update_product_status(
    product_ids: List[int], 
    new_status: str,
    config: RunnableConfig
) -> str:
    """
    Actualiza el estado de múltiples productos simultáneamente.
    Args:
        product_ids: Lista de IDs de productos a actualizar.
        new_status: Nuevo estado ('active', 'paused', 'archived').
    """
    raw_user_id = config.get("configurable", {}).get("user_id")
    if not raw_user_id:
        return "Error de Seguridad: No se identificó al usuario."
    try:
        user_id = int(raw_user_id)
    except (TypeError, ValueError):
        return "Error de Seguridad: Identificador de usuario inválido."

    valid_statuses = ["active", "paused", "archived"]
    if new_status not in valid_statuses:
        return f"Error: Estado inválido. Use: {', '.join(valid_statuses)}."
        
    from app.infrastructure.repositories.product import product_repo
    
    with Session(engine) as session:
        updated_count = product_repo.bulk_update_stock_status(session, user_id, product_ids, new_status)
        return f"Actualización masiva completada: {updated_count} productos cambiados a estado '{new_status}'."
