from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database.database import SessionLocal
from core.services.models import ServiceRequest
from core.professionals.models import Professional
from api.schemas.services import ServiceRequestCreate, ServiceRequestOut
from api.schemas.professionals import ProfessionalAccept
from core.pricing_engine.calculator import calcular_preco
from datetime import datetime
from api.schemas.services import PrecoEstimadoRequest, PrecoEstimadoOut
from core.pricing_engine.calculator import calcular_preco

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/solicitacoes/", response_model=ServiceRequestOut)
def criar_solicitacao(solicitacao: ServiceRequestCreate, db: Session = Depends(get_db)):
    nova = ServiceRequest(**solicitacao.dict())
    db.add(nova)
    db.commit()
    db.refresh(nova)
    return nova

@router.post("/profissionais/aceitar")
def aceitar_solicitacao(data: ProfessionalAccept, db: Session = Depends(get_db)):
    profissional = db.query(Professional).filter_by(id=data.professional_id).first()
    if not profissional or not profissional.is_available:
        raise HTTPException(status_code=400, detail="Profissional não disponível")

    solicitacao = db.query(ServiceRequest).filter_by(id=data.service_id).first()
    if not solicitacao or solicitacao.status != "pendente":
        raise HTTPException(status_code=400, detail="Solicitação não encontrada ou já aceita")

    solicitacao.status = "aceita"
    profissional.is_available = False
    db.commit()
    return {"message": "Solicitação aceita com sucesso"}

@router.post("/solicitacoes/", response_model=ServiceRequestOut)
def criar_solicitacao(solicitacao: ServiceRequestCreate, db: Session = Depends(get_db)):
    hora_atual = datetime.utcnow().hour
    preco_estimado = calcular_preco_base(hora=hora_atual, avaliacao=4.5)  # fixo por enquanto

    nova = ServiceRequest(**solicitacao.dict())
    nova.price = preco_estimado
    nova.status = "pendente"
    db.add(nova)
    db.commit()
    db.refresh(nova)
    return nova

@router.post("/preco/estimado", response_model=PrecoEstimadoOut)
def preco_estimado(request: PrecoEstimadoRequest, db: Session = Depends(get_db)):
    from core.professionals.models import Professional
    from core.services.models import ServiceRequest
    from datetime import datetime

    profissional = db.query(Professional).filter_by(id=request.profissional_id).first()
    if not profissional:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")

    demanda_pendente = db.query(ServiceRequest).filter(ServiceRequest.status == "pendente").count()
    hora_atual = datetime.utcnow().hour
    avaliacao = profissional.rating or 4.0


    preco = calcular_preco(hora=hora_atual, avaliacao=avaliacao, demandas_pendentes=demanda_pendente)
    return {"preco_estimado": preco}

