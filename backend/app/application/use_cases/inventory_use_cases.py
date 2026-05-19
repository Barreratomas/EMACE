from typing import List, Optional, Any, Dict
import io
import csv
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import Session, select
from app.domain.models import Product, User
from app.domain.schemas.inventory import ProductCreate, ProductUpdate
from app.domain.ports.repositories import IProductRepository

class InventoryUseCases:
    def __init__(self, product_repo: IProductRepository):
        self.product_repo = product_repo

    async def list_products(
        self, 
        session: AsyncSession, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100, 
        type: Optional[str] = None
    ) -> List[Product]:
        return await self.product_repo.get_all_async(
            session, user_id=user_id, skip=skip, limit=limit, type=type
        )

    async def create_product(
        self, 
        session: AsyncSession, 
        user_id: int, 
        product_in: ProductCreate
    ) -> Product:
        product = Product(**product_in.model_dump())
        product.user_id = user_id
        return await self.product_repo.create_async(session, product)

    async def get_product(
        self, 
        session: AsyncSession, 
        product_id: int, 
        user_id: int
    ) -> Product:
        return await self.product_repo.get_by_id_async(session, product_id, user_id)

    async def update_product(
        self,
        session: AsyncSession,
        product_id: int,
        user_id: int,
        product_update: ProductUpdate
    ) -> Product:
        product = await self.product_repo.get_by_id_async(session, product_id, user_id=user_id)
        if not product:
            return None
        return await self.product_repo.update_async(session, product, product_update)

    async def delete_product(
        self,
        session: AsyncSession,
        product_id: int,
        user_id: int
    ) -> bool:
        product = await self.product_repo.get_by_id_async(session, product_id, user_id=user_id)
        if not product:
            return False
        await self.product_repo.delete_async(session, product)
        return True

    async def adjust_stock(
        self,
        engine: Any,
        product_id: int,
        user_id: int,
        quantity_change: int
    ) -> Optional[Product]:
        with Session(engine) as sync_session:
            return self.product_repo.update_stock(sync_session, product_id, user_id, quantity_change)

    async def get_low_stock_products(
        self,
        engine: Any,
        user_id: int
    ) -> List[Product]:
        with Session(engine) as sync_session:
            return self.product_repo.check_low_stock(sync_session, user_id)

    async def bulk_update_status(
        self,
        engine: Any,
        user_id: int,
        product_ids: List[int],
        new_status: str
    ) -> int:
        with Session(engine) as sync_session:
            return self.product_repo.bulk_update_stock_status(sync_session, user_id, product_ids, new_status)

    async def import_products(
        self,
        session: AsyncSession,
        user_id: int,
        file_contents: bytes,
        filename: str,
        conflict_strategy: str = "skip",
        dry_run: bool = False
    ) -> Dict[str, Any]:
        if filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(file_contents))
        else:
            df = pd.read_excel(io.BytesIO(file_contents))

        df.columns = [c.strip().lower() for c in df.columns]

        required_cols = {'name', 'category', 'price'}
        missing_cols = required_cols - set(df.columns)
        if missing_cols:
            raise ValueError(f"Faltan columnas requeridas: {', '.join(missing_cols)}")

        preview_data = []
        imported_count = 0
        updated_count = 0
        skipped_count = 0
        errors = []

        # Obtener productos existentes para validación de conflictos
        existing_products = await self.product_repo.get_all_async(session, user_id=user_id, limit=10000)
        existing_map = {p.name.lower(): p for p in existing_products}

        for index, row in df.iterrows():
            try:
                name = str(row['name']).strip()
                category = str(row['category']).strip()
                try:
                    price = float(row['price'])
                except (ValueError, TypeError):
                    errors.append(f"Fila {index+2}: Precio inválido '{row['price']}'")
                    continue

                description = str(row.get('description', '')).strip()
                p_type = str(row.get('type', 'physical')).lower().strip()
                if p_type not in ['physical', 'service']:
                    p_type = 'physical'
                
                status_val = str(row.get('status', 'active')).lower().strip()
                if status_val not in ['active', 'paused', 'archived']:
                    status_val = 'active'

                stock = None
                if p_type == 'physical':
                    try:
                        stock = int(row.get('stock', 0))
                    except (ValueError, TypeError):
                        stock = 0

                min_stock = 5
                try:
                    min_stock = int(row.get('min_stock_threshold', 5))
                except (ValueError, TypeError):
                    min_stock = 5

                sla = str(row.get('sla', '')) if p_type == 'service' else None

                existing_p = existing_map.get(name.lower())
                
                if dry_run:
                    preview_data.append({
                        "name": name,
                        "category": category,
                        "price": price,
                        "type": p_type,
                        "status": status_val,
                        "stock": stock,
                        "conflict": "update" if existing_p else "new"
                    })
                    continue

                if existing_p:
                    if conflict_strategy == "skip":
                        skipped_count += 1
                        continue
                    elif conflict_strategy == "update":
                        existing_p.category = category
                        existing_p.price = price
                        existing_p.description = description
                        existing_p.type = p_type
                        existing_p.status = status_val
                        existing_p.stock = stock
                        existing_p.min_stock_threshold = min_stock
                        existing_p.sla = sla
                        session.add(existing_p)
                        updated_count += 1
                else:
                    new_product = Product(
                        user_id=user_id,
                        name=name,
                        category=category,
                        price=price,
                        description=description,
                        type=p_type,
                        status=status_val,
                        stock=stock,
                        min_stock_threshold=min_stock,
                        sla=sla
                    )
                    session.add(new_product)
                    imported_count += 1

            except Exception as e:
                errors.append(f"Fila {index+2}: {str(e)}")

        if not dry_run:
            await session.commit()

        return {
            "dry_run": dry_run,
            "total_processed": len(df),
            "imported": imported_count,
            "updated": updated_count,
            "skipped": skipped_count,
            "preview": preview_data if dry_run else None,
            "errors": errors if errors else None
        }

    def get_import_template(self, format: str = "csv") -> Dict[str, Any]:
        headers = [
            "name", "category", "price", "stock", "description", 
            "type", "status", "min_stock_threshold", "sla"
        ]
        sample_rows = [
            ["Laptop HP", "Hardware", "1200", "15", "Laptop de alto rendimiento", "physical", "active", "5", ""],
            ["Consultoría Seguridad", "Servicios", "1500", "0", "Auditoría de seguridad informática", "service", "paused", "", "48h report"]
        ]
        
        if format == "xlsx":
            buffer = io.BytesIO()
            df = pd.DataFrame(sample_rows, columns=headers)
            df.to_excel(buffer, index=False)
            buffer.seek(0)
            return {
                "content": buffer,
                "media_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "filename": "plantilla_inventario.xlsx"
            }
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows(sample_rows)
        return {
            "content": io.BytesIO(output.getvalue().encode("utf-8")),
            "media_type": "text/csv; charset=utf-8",
            "filename": "plantilla_inventario.csv"
        }
