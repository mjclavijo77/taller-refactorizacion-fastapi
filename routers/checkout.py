from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

# 1. Importamos las interfaces (Abstracciones)
from domain.interfaces import IInventoryRepository, IPaymentGateway, IDocumentService, INotificationStrategy

# 2. Importamos las implementaciones concretas
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

# --- CONTENEDOR DE DEPENDENCIAS (SINGLETONS) ---
# El inventario DEBE ser un singleton para que el Lock() funcione globalmente
inventory_repo_instance = InMemoryInventoryRepository()
payment_gateway_instance = StripePaymentGateway()
invoice_service_instance = InvoiceGeneratorService()

# --- FUNCIONES PROVEEDORAS (PROVIDERS) PARA INYECCIÓN ---
def get_inventory_repo() -> IInventoryRepository:
    return inventory_repo_instance

def get_payment_gateway() -> IPaymentGateway:
    return payment_gateway_instance

def get_invoice_service() -> IDocumentService:
    return invoice_service_instance

# Resolvemos qué estrategias de notificación usar según la petición
def get_notification_strategies(payload: CheckoutRequest) -> list[INotificationStrategy]:
    strategies = []
    for channel in payload.notify_via:
        if channel == "email":
            strategies.append(EmailNotificationStrategy())
        elif channel == "sms":
            strategies.append(SMSNotificationStrategy())
        elif channel == "webhook":
            strategies.append(WebhookNotificationStrategy())
    return strategies

# --- ENDPOINT REFACTORIZADO ---
@router.post("/process")
async def process_checkout(
    payload: CheckoutRequest,
    # INYECCIÓN DE DEPENDENCIAS: FastAPI se encarga de inyectar las instancias aquí
    tx_manager: IInventoryRepository = Depends(get_inventory_repo),
    payment_gateway: IPaymentGateway = Depends(get_payment_gateway),
    invoice_service: IDocumentService = Depends(get_invoice_service)
):
    # 1. Transacción de Inventario (Ahora asíncrona y segura)
    if not await tx_manager.begin_transaction(payload.product_id, payload.quantity):
        raise HTTPException(status_code=400, detail="Stock insuficiente o error de base de datos")
        
    total_amount = payload.quantity * 99.99
    
    # 2. Pasarela de Pago
    payment_success = await payment_gateway.execute_charge(payload.payment_token, total_amount)
    if not payment_success:
        await tx_manager.rollback_transaction(payload.product_id, payload.quantity)
        raise HTTPException(status_code=402, detail="Pago rechazado por la pasarela")
        
    # 3. Generación de Factura (Delegada a otro núcleo del procesador)
    order_id = f"TX-{payload.product_id}-12345"
    await invoice_service.generate_manifest(order_id, total_amount)
    
    # 4. Notificaciones (Usando el patrón Strategy iterado)
    strategies = get_notification_strategies(payload)
    for strategy in strategies:
        await strategy.send(payload.user_email, "Su orden ha sido procesada")
        
    return {"status": "success", "order_id": order_id}