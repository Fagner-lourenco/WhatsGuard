from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database.database import get_db
from api.schemas.avaliacoes import AvaliacaoCreate, AvaliacaoOut
from core.services.models import Avaliacao, ServiceRequest
from api.schemas.avaliacoes import AvaliacaoClienteCreate, AvaliacaoClienteOut
from core.services.models import AvaliacaoCliente

router = APIRouter(prefix="/avaliacoes", tags=["Avaliações"])

@router.post("/", response_model=AvaliacaoOut)
def criar_avaliacao(data: AvaliacaoCreate, db: Session = Depends(get_db)):
    # Verifica se a solicitação existe
    solicitacao = db.query(ServiceRequest).filter_by(id=data.solicitacao_id).first()
    if not solicitacao:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")

    # Verifica se já existe avaliação para a solicitação
    avaliacao_existente = db.query(Avaliacao).filter_by(solicitacao_id=data.solicitacao_id).first()
    if avaliacao_existente:
        raise HTTPException(status_code=400, detail="Esta solicitação já foi avaliada")

    nova_avaliacao = Avaliacao(
        profissional_id=data.profissional_id,
        solicitacao_id=data.solicitacao_id,
        nota=data.nota,
        comentario=data.comentario
    )
    db.add(nova_avaliacao)
    db.commit()
    db.refresh(nova_avaliacao)
    return nova_avaliacao

@router.get("/profissional/{profissional_id}", response_model=list[AvaliacaoOut])
def listar_avaliacoes_profissional(profissional_id: int, db: Session = Depends(get_db)):
    return db.query(Avaliacao).filter_by(profissional_id=profissional_id).all()


@router.post("/cliente/", response_model=AvaliacaoClienteOut)
def avaliar_cliente(data: AvaliacaoClienteCreate, db: Session = Depends(get_db)):
    avaliacao = AvaliacaoCliente(**data.dict())
    db.add(avaliacao)
    db.commit()
    db.refresh(avaliacao)
    return avaliacao
