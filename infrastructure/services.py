# Autor: Manuel Jose Clavijo - 13 de noviembre de 2026
# Servicios externos pasados a asincrono y patron Strategy en notificaciones

import asyncio
import math
import httpx
from concurrent.futures import ProcessPoolExecutor
from domain.interfaces import IPaymentGateway, INotificationStrategy, IDocumentService

class StripePaymentGateway(IPaymentGateway):
    async def execute_charge(self, token: str, amount: float) -> bool:
        try:
            # Cambie requests por httpx para hacer la peticion sin bloquear el servidor
            async with httpx.AsyncClient() as client:
                payload = {"token": token, "amount": amount, "key": "sk_test_mock_12345"}
                response = await client.post("https://api.stripe.mock/v1/charges", json=payload, timeout=5)
                return response.status_code == 200
        except Exception:
            return False

# Clases separadas por cada canal de notificacion (Strategy) 
class EmailNotificationStrategy(INotificationStrategy):
    async def send(self, destination: str, message: str) -> None:
        print(f"SMTP: Enviando a {destination}")
        await asyncio.sleep(0.1)

class SMSNotificationStrategy(INotificationStrategy):
    async def send(self, destination: str, message: str) -> None:
        print("Twilio API: Enviando SMS")
        await asyncio.sleep(0.2)

class WebhookNotificationStrategy(INotificationStrategy):
    async def send(self, destination: str, message: str) -> None:
        print("Webhook HTTP POST a endpoint del cliente")
        await asyncio.sleep(0.3)

# Funcion pesada del calculo del PDF separada para correrla aparte
def _calcular_pdf(order_id: str, amount: float) -> bytes:
    iterations = 5_000_000
    result = 0.0
    for i in range(iterations):
        result += math.sqrt(i) * math.sin(i)
    manifest_data = f"ORDER:{order_id}|TOTAL:{amount}|HASH:{result}"
    return manifest_data.encode('utf-8')

class InvoiceGeneratorService(IDocumentService):
    def __init__(self):
        # Ejecutor para que el for de 5 millones no trabe el hilo principal
        self.executor = ProcessPoolExecutor()

    async def generate_manifest(self, order_id: str, amount: float) -> bytes:
        loop = asyncio.get_running_loop()
        # Mandamos a calcular el PDF en otro proceso y esperamos con await
        return await loop.run_in_executor(
            self.executor, _calcular_pdf, order_id, amount
        )