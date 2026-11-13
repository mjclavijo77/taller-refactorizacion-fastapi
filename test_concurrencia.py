# Prueba asincrona para verificar que el Lock evita la condicion de carrera en el stock

import asyncio
from infrastructure.database import InMemoryInventoryRepository

async def probar_concurrencia_stock():
    repo = InMemoryInventoryRepository()
    
    # El producto PROD-A99 empieza con 10 unidades
    # Simulamos 5 clientes comprando 3 unidades al mismo tiempo (total 15 pedidas)
    # Con el Lock, solo 3 clientes deben poder comprar (9 unidades) y 2 deben fallar
    tareas = [
        repo.begin_transaction("PROD-A99", 3),
        repo.begin_transaction("PROD-A99", 3),
        repo.begin_transaction("PROD-A99", 3),
        repo.begin_transaction("PROD-A99", 3),
        repo.begin_transaction("PROD-A99", 3)
    ]
    
    resultados = await asyncio.gather(*tareas)
    
    compras_exitosas = resultados.count(True)
    compras_rechazadas = resultados.count(False)
    stock_final = repo._inventory["PROD-A99"]
    
    print(f"Compras exitosas: {compras_exitosas} (Esperado: 3)")
    print(f"Compras rechazadas: {compras_rechazadas} (Esperado: 2)")
    print(f"Stock final en base de datos: {stock_final} (Esperado: 1)")
    
    assert compras_exitosas == 3
    assert compras_rechazadas == 2
    assert stock_final == 1
    print("Prueba superada: No hubo condicion de carrera.")

if __name__ == "__main__":
    asyncio.run(probar_concurrencia_stock())