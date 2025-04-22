from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from core.database.database import get_db
from core.user_management.models import Client
from api.schemas.clients import ClientCreate, ClientOut
from typing import List
from api.schemas.services import ServiceRequestOut
from core.services.models import ServiceRequest

router = APIRouter(prefix="/clientes", tags=["Clientes"])

# POST /clientes/ - Criar cliente
@router.post("/", response_model=ClientOut)
def criar_cliente(cliente: ClientCreate, db: Session = Depends(get_db)):
    novo = Client(**cliente.dict())
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo

# GET /clientes/{client_id} - Buscar cliente por ID
@router.get("/{client_id}", response_model=ClientOut)
def get_cliente(client_id: int, db: Session = Depends(get_db)):
    cliente = db.query(Client).filter(Client.id == client_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail=f"Cliente com ID {client_id} não encontrado")
    return cliente



@router.get("/", response_model=List[ClientOut])
def listar_clientes(telefone: str | None = Query(None), db: Session = Depends(get_db)):
    query = db.query(Client)
    if telefone:
        query = query.filter(Client.telefone == telefone)
    return query.all()


@router.get("/{id}/historico", response_model=List[ServiceRequestOut])
def historico_cliente(id: int, db: Session = Depends(get_db)):
    return db.query(ServiceRequest).filter_by(client_id=id).all()
