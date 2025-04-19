
from core.services.models import ServiceRequest
from sqlalchemy.orm import Session
from datetime import datetime

def create_service_request(db: Session, client_id:int, location:str, price:float)->int:
    srv=ServiceRequest(client_id=client_id, location=location, price=price, status="pendente", created_at=datetime.utcnow())
    db.add(srv)
    db.commit()
    db.refresh(srv)
    return srv.id
