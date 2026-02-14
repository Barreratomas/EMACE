from typing import List, Optional
from sqlmodel import Session, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database.models import Product, ProductUpdate

class ProductRepository:
    # --- Sync Methods (Agents) ---
    def get_all(self, session: Session, user_id: int, skip: int = 0, limit: int = 100, type: Optional[str] = None) -> List[Product]:
        query = select(Product).where(Product.user_id == user_id)
        if type:
            query = query.where(Product.type == type)
        query = query.offset(skip).limit(limit)
        return session.exec(query).all()

    def get_by_id(self, session: Session, product_id: int, user_id: int) -> Optional[Product]:
        query = select(Product).where(Product.id == product_id, Product.user_id == user_id)
        return session.exec(query).first()

    def create(self, session: Session, product: Product) -> Product:
        # Nota: product ya debe tener user_id asignado desde el controlador/tool
        db_product = Product.model_validate(product)
        session.add(db_product)
        session.commit()
        session.refresh(db_product)
        return db_product

    def update(self, session: Session, db_product: Product, product_update: ProductUpdate) -> Product:
        # Nota: Se asume que db_product ya fue recuperado validando el user_id
        product_data = product_update.model_dump(exclude_unset=True)
        for key, value in product_data.items():
            setattr(db_product, key, value)
        session.add(db_product)
        session.commit()
        session.refresh(db_product)
        return db_product

    def delete(self, session: Session, db_product: Product) -> None:
        session.delete(db_product)
        session.commit()

    # --- Async Methods (API) ---
    async def get_all_async(self, session: AsyncSession, user_id: int, skip: int = 0, limit: int = 100, type: Optional[str] = None) -> List[Product]:
        query = select(Product).where(Product.user_id == user_id)
        if type:
            query = query.where(Product.type == type)
        query = query.offset(skip).limit(limit)
        result = await session.execute(query)
        return result.scalars().all()

    async def get_by_id_async(self, session: AsyncSession, product_id: int, user_id: int) -> Optional[Product]:
        query = select(Product).where(Product.id == product_id, Product.user_id == user_id)
        result = await session.execute(query)
        return result.scalars().first()

    async def create_async(self, session: AsyncSession, product: Product) -> Product:
        db_product = Product.model_validate(product)
        session.add(db_product)
        await session.commit()
        await session.refresh(db_product)
        return db_product

    async def update_async(self, session: AsyncSession, db_product: Product, product_update: ProductUpdate) -> Product:
        product_data = product_update.model_dump(exclude_unset=True)
        for key, value in product_data.items():
            setattr(db_product, key, value)
        session.add(db_product)
        await session.commit()
        await session.refresh(db_product)
        return db_product

    async def delete_async(self, session: AsyncSession, db_product: Product) -> None:
        await session.delete(db_product)
        await session.commit()

    # --- Stock Management Methods ---
    def check_low_stock(self, session: Session, user_id: int) -> List[Product]:
        """Obtiene productos con stock bajo (por debajo del umbral)"""
        query = select(Product).where(
            Product.user_id == user_id,
            Product.type == "physical",
            Product.status == "active",
            Product.stock.is_not(None),
            Product.min_stock_threshold.is_not(None),
            Product.stock < Product.min_stock_threshold
        )
        return session.exec(query).all()

    def update_stock(self, session: Session, product_id: int, user_id: int, quantity_change: int) -> Optional[Product]:
        """Actualiza el stock de un producto y devuelve el producto actualizado"""
        product = self.get_by_id(session, product_id, user_id)
        if not product or product.type != "physical" or product.stock is None:
            return None
        
        # Validar que no quede stock negativo
        new_stock = product.stock + quantity_change
        if new_stock < 0:
            return None
            
        product.stock = new_stock
        
        # Pausar automáticamente si el stock llega a 0
        if new_stock == 0:
            product.status = "paused"
            
        session.add(product)
        session.commit()
        session.refresh(product)
        return product

    def bulk_update_stock_status(self, session: Session, user_id: int, product_ids: List[int], new_status: str) -> int:
        """Actualiza el estado de múltiples productos"""
        query = select(Product).where(
            Product.user_id == user_id,
            Product.id.in_(product_ids)
        )
        products = session.exec(query).all()
        
        updated_count = 0
        for product in products:
            if product.status != new_status:
                product.status = new_status
                session.add(product)
                updated_count += 1
        
        if updated_count > 0:
            session.commit()
        
        return updated_count

product_repo = ProductRepository()
