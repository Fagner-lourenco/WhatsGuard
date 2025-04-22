# integrations/webhooks/mercadopago/handler.py
from fastapi import APIRouter, Request, HTTPException
from sqlalchemy.orm import Session
from core.database.database import SessionLocal
from core.services.models import ServiceRequest, StatusEnum
from core.professionals.models import Professional
from core.user_management.models import Client
from datetime import datetime
from integrations.whatsapp.client import send_text_v2

router = APIRouter(prefix="/webhook/mercadopago", tags=["Webhooks"])

@router.post("/")
async def mercadopago_webhook(payload: dict):
    if payload.get("type") != "payment":
        return {"msg": "Evento ignorado (não é pagamento)"}

    payment_data = payload.get("data", {})
    status = payment_data.get("status")
    metadata = payment_data.get("metadata", {})

    if status != "approved":
        return {"msg": "Pagamento não aprovado"}

    service_id = metadata.get("service_id")
    if not service_id:
        raise HTTPException(400, "Metadata inválida: service_id ausente")

    db: Session = SessionLocal()
    try:
        srv = db.query(ServiceRequest).filter_by(id=service_id).first()
        if not srv:
            raise HTTPException(404, "Solicitação não encontrada")

        if srv.status != StatusEnum.pendente:
            return {"msg": "Solicitação já processada"}

        # Encontrar profissional disponível com melhor nota
        prof = db.query(Professional).filter_by(is_available=True).order_by(Professional.rating.desc()).first()
        if not prof:
            raise HTTPException(400, "Nenhum profissional disponível no momento")

        # Atualizar solicitação
        srv.professional_id = prof.id
        srv.status = StatusEnum.aceito
        srv.accepted_at = datetime.utcnow()

        # Atualizar profissional
        prof.is_available = False

        db.commit()
        db.refresh(srv)

        # Notificar profissional
        await send_text_v2(prof.phone, f"📢 Nova missão aceita! Local: {srv.location}.")

        # Notificar cliente
        cliente = db.query(Client).filter_by(id=srv.client_id).first()
        if cliente:
            await send_text_v2(cliente.telefone, f"✅ Pagamento confirmado! {prof.name} está a caminho.")

        return {"msg": "Pagamento confirmado e profissional designado"}

    finally:
        db.close()