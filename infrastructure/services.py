import asyncio
import math
import httpx
from concurrent.futures import ProcessPoolExecutor
from domain.interfaces import IPaymentGateway, INotificationStrategy, IDocumentService


class StripePaymentGateway(IPaymentGateway):
    async def execute_charge(self, token: str, amount: float) -> bool:
        try:
            # Usamos httpx en lugar del requests sincrono que bloqueaba el servidor
            async with httpx.AsyncClient() as client:
                payload = {"token": token, "amount": amount, "key": "sk_test_mock_12345"}
                # Usamos una URL de prueba generica para no fallar
                response = await client.post("https://httpbin.org/post", json=payload, timeout=5)
                return response.status_code == 200
        except Exception:
            return False

# PATRON STRATEGY PARA NOTIFICACIONES 
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

# DELEGACIoN DE CPU INTENSIVA 
def _math_intensive_pdf_generation(order_id: str, amount: float) -> bytes:
    iterations = 5_000_000
    result = 0.0
    for i in range(iterations):
        result += math.sqrt(i) * math.sin(i)
    manifest_data = f"ORDER:{order_id}|TOTAL:{amount}|HASH:{result}"
    return manifest_data.encode('utf-8')

class InvoiceGeneratorService(IDocumentService):
    def __init__(self):
        # Creamos un pool de procesos para sacar la matematica del Event Loop principal
        self.executor = ProcessPoolExecutor(max_workers=2)

    async def generate_manifest(self, order_id: str, amount: float) -> bytes:
        loop = asyncio.get_running_loop()
        # Mandamos el calculo pesado a un núcleo del procesador diferente
        return await loop.run_in_executor(
            self.executor, _math_intensive_pdf_generation, order_id, amount
        )