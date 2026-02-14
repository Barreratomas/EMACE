from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from sqlmodel import select
from app.core.database.session import get_session
from app.core.database.models import Product, Order, OrderItem, Cart, CartItem, Invoice
import logging
from datetime import timedelta
from typing import List

logger = logging.getLogger(__name__)

@tool
def search_product_catalog(query: str, config: RunnableConfig) -> str:
    """
    Busca productos en el catálogo.
    Puede buscar por nombre, categoría o características.
    """
    user_id = config.get("configurable", {}).get("user_id")
    if not user_id:
        return "Error de Seguridad: No se identificó al usuario (Vendor)."

    session_gen = get_session()
    session = next(session_gen)
    try:
        # Búsqueda SQL simple (ILIKE) filtrada por user_id
        # En el futuro, esto podría ser búsqueda vectorial híbrida si indexamos productos
        statement = select(Product).where(
            Product.user_id == user_id,
            (Product.name.ilike(f"%{query}%")) | (Product.description.ilike(f"%{query}%")) | (Product.category.ilike(f"%{query}%"))
        )
        products = session.exec(statement).all()
        
        if not products:
            return f"No encontré productos que coincidan con '{query}' en tu catálogo."
            
        response = f"Productos encontrados para '{query}':\n"
        for p in products:
            stock_info = f" (Stock: {p.stock})" if p.type == 'physical' else ""
            response += f"- {p.name} (${p.price}) [{p.type}]: {p.description}{stock_info}\n"
            
        return response
    finally:
        session.close()

@tool
def check_stock(product_name: str, config: RunnableConfig) -> str:
    """
    Verifica la disponibilidad de un producto por nombre exacto o parcial.
    """
    user_id = config.get("configurable", {}).get("user_id")
    if not user_id:
        return "Error de Seguridad: No se identificó al usuario."

    session_gen = get_session()
    session = next(session_gen)
    try:
        statement = select(Product).where(
            Product.user_id == user_id,
            Product.name.ilike(f"%{product_name}%")
        )
        products = session.exec(statement).all()
        
        if not products:
            return f"No encontré el producto '{product_name}'."
            
        if len(products) > 1:
            names = ", ".join([p.name for p in products])
            return f"Encontré varios productos similares: {names}. Por favor sé más específico."
            
        product = products[0]
        if product.type == 'service':
            return f"El producto '{product.name}' es un servicio y está disponible."
            
        return f"El producto '{product.name}' tiene {product.stock} unidades en stock."
    finally:
        session.close()

@tool
def create_order(product_names_and_quantities: List[dict], config: RunnableConfig) -> str:
    """
    Crea un pedido para el cliente actual. 
    Recibe una lista de diccionarios con 'product_name' y 'quantity'.
    Ejemplo: [{"product_name": "Laptop", "quantity": 1}, {"product_name": "Mouse", "quantity": 2}]
    """
    user_id = config.get("configurable", {}).get("user_id")
    customer_id = config.get("configurable", {}).get("customer_id")
    
    if not user_id or not customer_id:
        return "Error: No se pudo identificar el contexto de la venta o el cliente."

    session_gen = get_session()
    session = next(session_gen)
    try:
        total_amount = 0.0
        order_items_to_create = []
        
        for item in product_names_and_quantities:
            name = item.get("product_name")
            qty = item.get("quantity", 1)
            
            # Buscar producto
            statement = select(Product).where(Product.user_id == user_id, Product.name.ilike(f"%{name}%"))
            product = session.exec(statement).first()
            
            if not product:
                return f"Error: No encontré el producto '{name}' en el inventario."
            
            if product.type == 'physical' and (product.stock is None or product.stock < qty):
                return f"Error: No hay suficiente stock para '{product.name}'. Disponible: {product.stock}"
            
            item_price = product.price * qty
            total_amount += item_price
            
            order_items_to_create.append({
                "product_id": product.id,
                "quantity": qty,
                "unit_price": product.price
            })
            
            # Descontar stock si es físico
            if product.type == 'physical':
                product.stock -= qty
                session.add(product)

        # Crear la orden
        new_order = Order(
            customer_id=customer_id,
            user_id=user_id,
            total_amount=total_amount,
            status="confirmed" # Por ahora lo confirmamos directamente
        )
        session.add(new_order)
        session.commit()
        session.refresh(new_order)
        
        # Crear los items de la orden
        for item_data in order_items_to_create:
            order_item = OrderItem(
                order_id=new_order.id,
                **item_data
            )
            session.add(order_item)
        
        session.commit()
        return f"✅ ¡Pedido creado con éxito! Orden #{new_order.id}. Total: ${total_amount}. Los productos están siendo preparados."
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error creando pedido: {e}")
        return f"Hubo un error procesando tu pedido: {str(e)}"
    finally:
        session.close()

@tool
def add_to_cart(product_name: str, quantity: int = 1, config: RunnableConfig = None) -> str:
    """
    Añade un producto al carrito de compras del cliente.
    """
    user_id = config.get("configurable", {}).get("user_id")
    customer_id = config.get("configurable", {}).get("customer_id")
    if not customer_id: return "Error: No se identificó al cliente."

    session_gen = get_session()
    session = next(session_gen)
    try:
        # 1. Buscar producto
        stmt = select(Product).where(Product.user_id == user_id, Product.name.ilike(f"%{product_name}%"))
        product = session.exec(stmt).first()
        if not product: return f"No encontré el producto '{product_name}'."
        if product.type == 'physical' and (product.stock or 0) < quantity:
            return f"Stock insuficiente para {product.name}. Disponible: {product.stock}"

        # 2. Obtener o crear carrito
        stmt_cart = select(Cart).where(Cart.customer_id == customer_id)
        cart = session.exec(stmt_cart).first()
        if not cart:
            cart = Cart(customer_id=customer_id, user_id=user_id)
            session.add(cart)
            session.commit()
            session.refresh(cart)

        # 3. Añadir item
        stmt_item = select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == product.id)
        item = session.exec(stmt_item).first()
        if item:
            item.quantity += quantity
        else:
            item = CartItem(cart_id=cart.id, product_id=product.id, quantity=quantity)
        
        session.add(item)
        session.commit()
        return f"Añadido {quantity}x {product.name} al carrito."
    finally:
        session.close()

@tool
def view_cart(config: RunnableConfig) -> str:
    """
    Muestra los productos actuales en el carrito del cliente.
    """
    customer_id = config.get("configurable", {}).get("customer_id")
    session_gen = get_session()
    session = next(session_gen)
    try:
        stmt = select(Cart).where(Cart.customer_id == customer_id)
        cart = session.exec(stmt).first()
        if not cart: return "Tu carrito está vacío."

        stmt_items = select(CartItem, Product).join(Product).where(CartItem.cart_id == cart.id)
        items = session.exec(stmt_items).all()
        if not items: return "Tu carrito está vacío."

        res = "🛒 Tu Carrito:\n"
        total = 0
        for item, prod in items:
            subtotal = prod.price * item.quantity
            total += subtotal
            res += f"- {item.quantity}x {prod.name} (${prod.price} c/u) = ${subtotal}\n"
        res += f"\nTotal: ${total}"
        return res
    finally:
        session.close()

@tool
def checkout_cart(config: RunnableConfig) -> str:
    """
    Procesa el carrito actual y crea un pedido formal.
    """
    user_id = config.get("configurable", {}).get("user_id")
    customer_id = config.get("configurable", {}).get("customer_id")
    session_gen = get_session()
    session = next(session_gen)
    try:
        stmt = select(Cart).where(Cart.customer_id == customer_id)
        cart = session.exec(stmt).first()
        if not cart: return "No tienes un carrito activo."

        stmt_items = select(CartItem, Product).join(Product).where(CartItem.cart_id == cart.id)
        items = session.exec(stmt_items).all()
        if not items: return "Tu carrito está vacío."

        # Crear Orden
        total = sum(p.price * i.quantity for i, p in items)
        order = Order(customer_id=customer_id, user_id=user_id, total_amount=total, status="confirmed")
        session.add(order)
        session.commit()
        session.refresh(order)

        # Crear Items de Orden y descontar stock
        for i, p in items:
            oi = OrderItem(order_id=order.id, product_id=p.id, quantity=i.quantity, unit_price=p.price)
            if p.type == 'physical':
                p.stock -= i.quantity
                session.add(p)
            session.add(oi)
            session.delete(i) # Limpiar carrito

        # Auto-generar Factura
        invoice = Invoice(
            customer_id=customer_id,
            user_id=user_id,
            amount=total,
            status="pending",
            due_date=__import__('datetime').datetime.now(__import__('datetime').timezone.utc).replace(tzinfo=None) + timedelta(days=7)
        )
        session.add(invoice)
        
        session.commit()
        return f"✅ ¡Pedido confirmado! Orden #{order.id} por ${total}. Se ha generado la Factura #{invoice.id} pendiente de pago."
    except Exception as e:
        session.rollback()
        return f"Error en checkout: {str(e)}"
    finally:
        session.close()
