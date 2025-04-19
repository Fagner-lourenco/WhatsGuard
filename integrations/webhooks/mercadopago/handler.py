# integrations/webhooks/mercadopago/handler.py
from fastapi import APIRouter, Request, HTTPException
from core.services.models import ServiceRequest
from core.database.database import SessionLocal

router = APIRouter(prefix="/webhook/mercadopago", tags=["Webhooks"])

@router.post("/")
async def mercadopago_webhook(payload: dict):
    if payload.get("type") != "payment" or payload["data"]["status"] != "approved":
        return "ignored"

    service_id = payload["data"]["metadata"]["service_id"]
    db = SessionLocal()
    srv = db.query(ServiceRequest).filter_by(id=service_id).first()
    if not srv:
        db.close()
        raise HTTPException(404, "service not found")

    srv.payment_status = "paid"
    db.commit()
    db.close()
    return "ok"
