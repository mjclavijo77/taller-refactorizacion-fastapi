import asyncio
from domain.interfaces import IInventoryRepository

class InMemoryInventoryRepository(IInventoryRepository):
    def __init__(self):
        self._inventory = {"PROD-A99": 10, "PROD-B88": 2}
        self._lock = asyncio.Lock()  # El candado que resuelve la condición de carrera

    async def begin_transaction(self, product_id: str, quantity: int) -> bool:
        async with self._lock:  # Solo una peticion puede entrar a esta zona a la vez
            current_stock = self._inventory.get(product_id, 0)
            if current_stock >= quantity:
                await asyncio.sleep(0.5)  # Pausa asincrona ya no bloquea el servidor
                self._inventory[product_id] = current_stock - quantity
                return True
            return False

    async def rollback_transaction(self, product_id: str, quantity: int) -> None:
        async with self._lock:
            current_stock = self._inventory.get(product_id, 0)
            self._inventory[product_id] = current_stock + quantity