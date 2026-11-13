# Autor: Manuel Jose Clavijo - 13 de noviembre de 2026
# Rutas de checkout usando Depends para no instanciar clases adentro

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from domain.interfaces import IInventoryRepository, IPaymentGateway, IDocumentService, INotificationStrategy
from infrastructure.database import InMemoryInventoryRepository
from infrastructure.services import (
    StripePaymentGateway, 
    InvoiceGeneratorService, 
    EmailNotificationStrategy, 
    SMSNotificationStrategy, 
    WebhookNotificationStrategy
)

router = APIRouter()

class CheckoutRequest(BaseModel):
    product_id: str
    quantity: int
    payment_token: str
    user_email: str
    notify_via: list[str]

# Instancias globales para que el inventario guarde los datos entre peticiones
db_repo = InMemoryInventoryRepository()
pasarela_pago = StripePaymentGateway()
servicio_facturas = InvoiceGeneratorService()

# Funciones para inyectar con Depends en la ruta
def get_inventory_repo() -> IInventoryRepository:
    return db_repo

def get_payment_gateway() -> IPaymentGateway:
    return pasarela_pago

def get_invoice_service() -> IDocumentService:
    return servicio_facturas

# Diccionario para elegir el canal sin hacer cadena de if/elif en el servicio
MAPA_CANALES = {
    "email": EmailNotificationStrategy,
    "sms": SMSNotificationStrategy,
    "webhook": WebhookNotificationStrategy
}

def obtener_estrategias_notificacion(canales: list[str]) -> list[INotificationStrategy]:
    lista = []
    for canal in canales:
        if canal not in MAPA_CANALES:
            raise ValueError(f"Canal no soportado: {canal}")
        lista.append(MAPA_CANALES[canal]())
    return lista

@router.post("/process")
async def process_checkout(
    payload: CheckoutRequest,
    # Inyeccion de dependencias con FastAPI
    tx_manager: IInventoryRepository = Depends(get_inventory_repo),
    payment_gateway: IPaymentGateway = Depends(get_payment_gateway),
    invoice_service: IDocumentService = Depends(get_invoice_service)
):
    # 1 Verificamos y descontamos stock de forma asincrona
    if not await tx_manager.begin_transaction(payload.product_id, payload.quantity):
        raise HTTPException(status_code=400, detail="Stock insuficiente o error de base de datos")
        
    total_amount = payload.quantity * 99.99
    
    # 2 Cobramos por la pasarela de pago
    payment_success = await payment_gateway.execute_charge(payload.payment_token, total_amount)
    if not payment_success:
        await tx_manager.rollback_transaction(payload.product_id, payload.quantity)
        raise HTTPException(status_code=402, detail="Pago rechazado por la pasarela")
        
    # 3 Generamos la factura sin bloquear el bucle de eventos
    order_id = f"TX-{payload.product_id}-12345"
    await invoice_service.generate_manifest(order_id, total_amount)
    
    # 4 Enviamos las alertas segun los canales que pidio el usuario
    estrategias = obtener_estrategias_notificacion(payload.notify_via)
    for estrategia in estrategias:
        await estrategia.send(payload.user_email, "Su orden ha sido procesada")
        
    return {"status": "success", "order_id": order_id}