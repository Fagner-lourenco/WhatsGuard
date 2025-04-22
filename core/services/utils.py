from core.services.models import ServiceRequest, StatusEnum
from sqlalchemy.orm import Session
from datetime import datetime

# Criação direta de uma solicitação de serviço com preço definido
def create_service_request(db: Session, client_id: int, location: str, price: float) -> int:
    srv = ServiceRequest(
        client_id=client_id,
        location=location,
        price=price,
        status=StatusEnum.pendente,
        created_at=datetime.utcnow()
    )
    db.add(srv)
    db.commit()
    db.refresh(srv)
    return srv.id

# Função para montar os dados do dashboard geral
def get_dashboard_geral(db: Session):
    total = db.query(ServiceRequest).count()
    pendentes = db.query(ServiceRequest).filter_by(status=StatusEnum.pendente).count()
    aceitos = db.query(ServiceRequest).filter_by(status=StatusEnum.aceito).count()
    finalizados = db.query(ServiceRequest).filter_by(status=StatusEnum.finalizado).count()

    return {
        "total_solicitacoes": total,
        "pendentes": pendentes,
        "aceitos": aceitos,
        "finalizados": finalizados
    }
