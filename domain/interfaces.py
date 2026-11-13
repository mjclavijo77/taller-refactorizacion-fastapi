# Interfaces abstractas para separar la logica y cumplir con DIP
from abc import ABC, abstractmethod

class IInventoryRepository(ABC):
    @abstractmethod
    async def begin_transaction(self, product_id: str, quantity: int) -> bool:
        pass
    
    @abstractmethod
    async def rollback_transaction(self, product_id: str, quantity: int) -> None:
        pass

class IPaymentGateway(ABC):
    @abstractmethod
    async def execute_charge(self, token: str, amount: float) -> bool:
        pass

# Molde base para las notificaciones y no usar tantos if/elif
class INotificationStrategy(ABC):
    @abstractmethod
    async def send(self, destination: str, message: str) -> None:
        pass

class IDocumentService(ABC):
    @abstractmethod
    async def generate_manifest(self, order_id: str, amount: float) -> bytes:
        pass