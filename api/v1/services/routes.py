from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from core.database.database import get_db
from core.services.models import ServiceRequest, StatusEnum
from core.professionals.models import Professional
from api.schemas.services import (
    ServiceRequestCreate,
    ServiceRequestOut,
    PrecoEstimadoRequest,
    PrecoEstimadoOut
)
from api.schemas.professionals import ProfessionalAccept
from core.pricing_engine.calculator import calcular_preco
from core.services.utils import get_dashboard_geral
from integrations.whatsapp.client import send_text_v2

router = APIRouter(prefix="/solicitacoes", tags=["Solicitações de Serviço"])


# POST /solicitacoes/ - Criar nova solicitação
@router.post("/", response_model=ServiceRequestOut)
def criar_solicitacao(solicitacao: ServiceRequestCreate, db: Session = Depends(get_db)):
    hora_atual = datetime.utcnow().hour
    demandas = db.query(ServiceRequest).filter(ServiceRequest.status == StatusEnum.pendente).count()

    preco_estimado = calcular_preco(
        hora=hora_atual,
        avaliacao=4.5,
        demandas_pendentes=demandas
    )

    nova = ServiceRequest(**solicitacao.dict())
    nova.price = preco_estimado
    nova.status = StatusEnum.pendente

    db.add(nova)
    db.commit()
    db.refresh(nova)
    return nova



# POST /aceitar - Profissional aceita solicitação
@router.post("/aceitar", response_model=ServiceRequestOut)
def aceitar_solicitacao(data: ProfessionalAccept, db: Session = Depends(get_db)):
    profissional = db.query(Professional).filter_by(id=data.professional_id).first()
    if not profissional or not profissional.is_available:
        raise HTTPException(status_code=400, detail="Profissional não disponível")

    solicitacao = db.query(ServiceRequest).filter_by(id=data.solicitacao_id).first()
    if not solicitacao or solicitacao.status != StatusEnum.pendente:
        raise HTTPException(status_code=400, detail="Solicitação indisponível")

    solicitacao.status = StatusEnum.aceito
    solicitacao.professional_id = data.professional_id
    solicitacao.accepted_at = datetime.utcnow()
    profissional.is_available = False

    db.commit()
    db.refresh(solicitacao)
    return solicitacao


# GET / - Lista todas as solicitações, com filtro opcional por profissional
@router.get("/", response_model=List[ServiceRequestOut])
def listar_solicitacoes(prof_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(ServiceRequest)
    if prof_id:
        query = query.filter(ServiceRequest.professional_id == prof_id)
    return query.all()


# GET /pendentes - Apenas solicitações pendentes
@router.get("/pendentes", response_model=List[ServiceRequestOut])
def listar_pendentes(db: Session = Depends(get_db)):
    return db.query(ServiceRequest).filter(ServiceRequest.status == StatusEnum.pendente).all()


# PATCH /{id}/finalizar - Finalizar atendimento
@router.patch("/{solicitacao_id}/finalizar", response_model=ServiceRequestOut)
def finalizar_solicitacao(solicitacao_id: int, db: Session = Depends(get_db)):
    solicitacao = db.query(ServiceRequest).filter_by(id=solicitacao_id).first()
    if not solicitacao:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")

    solicitacao.status = StatusEnum.finalizado
    solicitacao.finished_at = datetime.utcnow()
    db.commit()
    db.refresh(solicitacao)
    return solicitacao

@router.post("/preco/estimado", response_model=PrecoEstimadoOut)
def preco_estimado(request: PrecoEstimadoRequest, db: Session = Depends(get_db)):
    profissional = db.query(Professional).filter_by(id=request.profissional_id).first()
    if not profissional:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")

    pendentes = db.query(ServiceRequest).filter(ServiceRequest.status == StatusEnum.pendente).count()
    hora_atual = datetime.utcnow().hour
    avaliacao = profissional.rating or 4.0

    preco = calcular_preco(hora=hora_atual, avaliacao=avaliacao, demandas_pendentes=pendentes)
    return {"preco_estimado": preco}


# GET /dashboard/geral - KPIs gerais
@router.get("/dashboard/geral")
def dashboard_geral(db: Session = Depends(get_db)):
    return get_dashboard_geral(db)

@router.get("/profissional/{prof_id}", response_model=List[ServiceRequestOut])
def listar_solicitacoes_por_profissional(prof_id: int, db: Session = Depends(get_db)):
    return db.query(ServiceRequest).filter(ServiceRequest.professional_id == prof_id).all()

# PATCH /{solicitacao_id}/finalizar - Finalizar atendimento e notificar
@router.patch("/{solicitacao_id}/finalizar", response_model=ServiceRequestOut)
async def finalizar_solicitacao(solicitacao_id: int, db: Session = Depends(get_db)):
    solicitacao = db.query(ServiceRequest).filter_by(id=solicitacao_id).first()
    if not solicitacao:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")

    solicitacao.status = StatusEnum.finalizado
    solicitacao.finished_at = datetime.utcnow()
    db.commit()

    # Notificar cliente
    cliente = db.query(Client).filter_by(id=solicitacao.client_id).first()
    if cliente:
        texto = "Seu serviço foi finalizado. Deseja avaliá-lo?"
        await send_text_v2(cliente.telefone, texto)

    db.refresh(solicitacao)
    return solicitacao