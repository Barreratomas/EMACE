from abc import ABC, abstractmethod
from typing import List, Optional, Any, Dict
from app.domain.models import (
    User, Role, RefreshToken, IAMPolicy, Product, ProductUpdate, 
    VendorAccessState, BillingEvent, VendorTelegramIntegration
)

class IAuthRepository(ABC):
    @abstractmethod
    async def get_user_by_email(self, session: Any, email: str) -> Optional[User]:
        pass

    @abstractmethod
    async def get_user_by_id(self, session: Any, user_id: int) -> Optional[User]:
        pass

    @abstractmethod
    async def create_user(self, session: Any, user: User) -> User:
        pass

    @abstractmethod
    async def update_user(self, session: Any, db_user: User, user_data: dict) -> User:
        pass

    @abstractmethod
    async def get_role_by_id(self, session: Any, role_id: int) -> Optional[Role]:
        pass

    @abstractmethod
    async def get_role_by_name(self, session: Any, name: str) -> Optional[Role]:
        pass

    @abstractmethod
    async def create_role(self, session: Any, role: Role) -> Role:
        pass

    @abstractmethod
    async def get_all_roles(self, session: Any) -> List[Role]:
        pass

    @abstractmethod
    async def get_users_by_parent(self, session: Any, parent_id: int) -> List[User]:
        pass

    @abstractmethod
    async def get_child_user_by_id(self, session: Any, parent_id: int, child_id: int) -> Optional[User]:
        pass

    @abstractmethod
    async def get_policy_by_name(self, session: Any, name: str) -> Optional[IAMPolicy]:
        pass

    @abstractmethod
    async def create_policy(self, session: Any, policy: IAMPolicy) -> IAMPolicy:
        pass

    @abstractmethod
    async def get_policies_by_names(self, session: Any, names: List[str]) -> List[IAMPolicy]:
        pass

    @abstractmethod
    async def create_refresh_token(self, session: Any, token_data: RefreshToken) -> RefreshToken:
        pass

    @abstractmethod
    async def get_refresh_token(self, session: Any, token: str) -> Optional[RefreshToken]:
        pass

    @abstractmethod
    async def revoke_refresh_token(self, session: Any, token_id: int) -> None:
        pass

    @abstractmethod
    async def revoke_all_user_tokens(self, session: Any, user_id: int) -> None:
        pass

    @abstractmethod
    async def rotate_refresh_token(self, session: Any, old_token_id: int, new_token_data: RefreshToken) -> RefreshToken:
        pass

class IProductRepository(ABC):
    @abstractmethod
    def get_all(self, session: Any, user_id: int, skip: int = 0, limit: int = 100, type: Optional[str] = None) -> List[Product]:
        pass

    @abstractmethod
    def get_by_id(self, session: Any, product_id: int, user_id: int) -> Optional[Product]:
        pass

    @abstractmethod
    def create(self, session: Any, product: Product) -> Product:
        pass

    @abstractmethod
    async def get_all_async(self, session: Any, user_id: int, skip: int = 0, limit: int = 100, type: Optional[str] = None) -> List[Product]:
        pass

    @abstractmethod
    async def get_by_id_async(self, session: Any, product_id: int, user_id: int) -> Optional[Product]:
        pass

    @abstractmethod
    async def create_async(self, session: Any, product: Product) -> Product:
        pass

    @abstractmethod
    async def update_async(self, session: Any, db_product: Product, product_update: ProductUpdate) -> Product:
        pass

    @abstractmethod
    async def count_active_products(self, session: Any, user_id: int) -> int:
        pass

    @abstractmethod
    async def count_low_stock_products(self, session: Any, user_id: int) -> int:
        pass

    @abstractmethod
    async def count_categories(self, session: Any, user_id: int) -> int:
        pass

    @abstractmethod
    async def get_estimated_inventory_value(self, session: Any, user_id: int) -> float:
        pass

    @abstractmethod
    async def delete_async(self, session: Any, db_product: Product) -> None:
        pass

    @abstractmethod
    def check_low_stock(self, session: Any, user_id: int) -> List[Product]:
        pass

    @abstractmethod
    def update_stock(self, session: Any, product_id: int, user_id: int, quantity_change: int) -> Optional[Product]:
        pass

    @abstractmethod
    def bulk_update_stock_status(self, session: Any, user_id: int, product_ids: List[int], new_status: str) -> int:
        pass

class IBillingRepository(ABC):
    @abstractmethod
    async def get_access_state(self, session: Any, vendor_id: int) -> Optional[VendorAccessState]:
        pass

    @abstractmethod
    async def upsert_access_state(self, session: Any, vendor_id: int, updates: Dict[str, Any], actor_user_id: Optional[int] = None) -> VendorAccessState:
        pass

    @abstractmethod
    async def save_billing_event(self, session: Any, vendor_id: int, event_type: str, mp_event_id: Optional[str], raw_payload: Optional[dict], normalized: Optional[dict]) -> BillingEvent:
        pass

    @abstractmethod
    async def get_paid_invoices_summary(self, session: Any, user_id: int, since: Optional[Any] = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def count_customers(self, session: Any, user_id: int) -> int:
        pass

    @abstractmethod
    async def get_unpaid_invoices_summary(self, session: Any, user_id: int) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def count_orders_by_status(self, session: Any, user_id: int, status: str, since: Optional[Any] = None) -> int:
        pass

class ITelegramRepository(ABC):
    @abstractmethod
    async def get_by_vendor_id(self, session: Any, vendor_id: int) -> Optional[VendorTelegramIntegration]:
        pass

    @abstractmethod
    async def get_by_bot_username(self, session: Any, bot_username: str) -> Optional[VendorTelegramIntegration]:
        pass

    @abstractmethod
    async def get_all_active(self, session: Any) -> List[VendorTelegramIntegration]:
        pass

    @abstractmethod
    async def upsert(
        self,
        session: Any,
        vendor_id: int,
        bot_username: str,
        bot_token_encrypted: str,
        webhook_secret: str,
    ) -> VendorTelegramIntegration:
        pass

class IKnowledgePort(ABC):
    @abstractmethod
    def ingest_file(self, file_path: str, user_id: int) -> None:
        pass

    @abstractmethod
    def list_documents(self, user_id: int) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_vendor_usage_bytes(self, user_id: int) -> int:
        pass

    @abstractmethod
    def delete_document(self, user_id: int, source_name: str) -> bool:
        pass

class IAuditRepository(ABC):
    @abstractmethod
    async def get_logs_by_user(self, session: Any, user_id: int, limit: int = 50, offset: int = 0) -> List[Any]:
        pass

    @abstractmethod
    async def count_logs_by_user(self, session: Any, user_id: int, since: Optional[Any] = None) -> int:
        pass

    @abstractmethod
    async def count_distinct_agents(self, session: Any, user_id: int, since: Optional[Any] = None) -> int:
        pass

    @abstractmethod
    async def save_log(self, session: Any, log: Any) -> Any:
        pass
