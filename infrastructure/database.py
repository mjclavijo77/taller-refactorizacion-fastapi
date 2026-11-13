# Autor: Manuel Jose Clavijo - 13 de noviembre de 2026
# Manejo del inventario en memoria corrigiendo el problema de concurrencia

import asyncio
from domain.interfaces import IInventoryRepository

class InMemoryInventoryRepository(IInventoryRepository):
    def __init__(self):
        self._inventory = {"PROD-A99": 10, "PROD-B88": 2}
        # Uso Lock de asyncio para que dos compras al tiempo no pisen el stock
        self._lock = asyncio.Lock()

    async def begin_transaction(self, product_id: str, quantity: int) -> bool:
        # Bloqueamos mientras revisa y descuenta el inventario
        async with self._lock:
            current_stock = self._inventory.get(product_id, 0)
            if current_stock >= quantity:
                # Cambie time.sleep por asyncio.sleep para no congelar FastAPI
                await asyncio.sleep(0.5)
                self._inventory[product_id] = current_stock - quantity
                return True
            return False

    async def rollback_transaction(self, product_id: str, quantity: int) -> None:
        # Si falla el pago devolvemos los productos al stock de forma segura
        async with self._lock:
            current_stock = self._inventory.get(product_id, 0)
            self._inventory[product_id] = current_stock + quantity