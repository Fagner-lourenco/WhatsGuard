from fastapi import APIRouter, HTTPException, Depends, Request, UploadFile, File
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
from pathlib import Path

from core.professionals.models import Professional, DocumentoProfissional
from core.services.models import ServiceRequest, StatusEnum
from core.database.database import get_db
from api.schemas.services import ServiceRequestOut
from api.schemas.professionals import (
    ProfessionalCreate,
    ProfessionalOut,
    AvaliacaoInput
)
from integrations.whatsapp.client import send_text_v2
from core.fsm.state_manager import set_state

router = APIRouter(prefix="/profissionais", tags=["Profissionais"])

UPLOAD_DIR = Path("uploads/documentos")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/", response_model=ProfessionalOut)
def criar_profissional(prof: ProfessionalCreate, db: Session = Depends(get_db)):
    existente = db.query(Professional).filter_by(cpf=prof.cpf).first()
    if existente:
        raise HTTPException(status_code=400, detail="Profissional com este CPF já cadastrado")

    novo = Professional(
        name=prof.name,
        cpf=prof.cpf,
        phone=prof.phone,
        is_available=True,
        rating=4.5,
        total_atendimentos=0
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo

@router.get("/", response_model=List[ProfessionalOut])
def listar_profissionais(db: Session = Depends(get_db)):
    return db.query(Professional).all()

@router.patch("/{id}/avaliar", response_model=ProfessionalOut)
def avaliar_profissional(id: int, entrada: AvaliacaoInput, db: Session = Depends(get_db)):
    profissional = db.query(Professional).filter_by(id=id).first()
    if not profissional:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")

    total = profissional.total_atendimentos
    nova_media = ((profissional.rating * total) + entrada.nova_nota) / (total + 1)

    profissional.rating = nova_media
    profissional.total_atendimentos += 1

    db.commit()
    db.refresh(profissional)
    return profissional

@router.patch("/{id}/disponibilidade")
def atualizar_disponibilidade(id: int, status: bool, db: Session = Depends(get_db)):
    profissional = db.query(Professional).filter_by(id=id).first()
    if not profissional:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")

    profissional.is_available = status
    db.commit()
    db.refresh(profissional)
    return {"msg": f"Profissional {'disponível' if status else 'indisponível'} com sucesso"}

@router.get("/ranking", response_model=List[ProfessionalOut])
def ranking_profissionais(db: Session = Depends(get_db)):
    return db.query(Professional).order_by(Professional.rating.desc()).all()

@router.get("/dashboard", tags=["Dashboards"])
def dashboard_profissionais(db: Session = Depends(get_db)):
    query = (
        db.query(
            Professional.id,
            Professional.name,
            Professional.rating,
            Professional.total_atendimentos
        )
        .order_by(Professional.total_atendimentos.desc())
        .all()
    )

    return [
        {
            "id": p.id,
            "nome": p.name,
            "nota": p.rating,
            "atendimentos": p.total_atendimentos
        }
        for p in query
    ]

@router.get("/{prof_id}", response_model=ProfessionalOut)
def get_profissional(prof_id: int, db: Session = Depends(get_db)):
    prof = db.query(Professional).filter_by(id=prof_id).first()
    if not prof:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")
    return prof

@router.get("/{id}/historico", response_model=List[ServiceRequestOut])
def historico_profissional(id: int, db: Session = Depends(get_db)):
    profissional = db.query(Professional).filter_by(id=id).first()
    if not profissional:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")

    servicos = (
        db.query(ServiceRequest)
        .filter(
            ServiceRequest.professional_id == id,
            ServiceRequest.status.in_([StatusEnum.aceito, StatusEnum.finalizado])
        )
        .order_by(ServiceRequest.created_at.desc())
        .all()
    )
    return servicos

@router.post("/{id}/checkin")
def checkin_profissional(id: int, request: Request, db: Session = Depends(get_db)):
    profissional = db.query(Professional).filter_by(id=id).first()
    if not profissional:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")

    profissional.ultimo_aceite = datetime.utcnow()
    profissional.is_available = True
    db.commit()
    return {"msg": "Check-in registrado com sucesso", "hora": profissional.ultimo_aceite}

@router.post("/{id}/checkout")
def checkout_profissional(id: int, request: Request, db: Session = Depends(get_db)):
    profissional = db.query(Professional).filter_by(id=id).first()
    if not profissional:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")

    profissional.is_available = False
    db.commit()
    return {"msg": "Checkout registrado. Profissional indisponível."}

@router.post("/{id}/documentos")
def upload_documentos(
    id: int,
    arquivo: UploadFile = File(...),
    tipo: str = "outro",
    db: Session = Depends(get_db)
):
    profissional = db.query(Professional).filter_by(id=id).first()
    if not profissional:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")

    extensao = Path(arquivo.filename).suffix
    if extensao.lower() not in [".pdf", ".jpg", ".jpeg", ".png"]:
        raise HTTPException(status_code=400, detail="Formato de arquivo não permitido")

    destino = UPLOAD_DIR / f"prof_{id}_{arquivo.filename}"
    with open(destino, "wb") as buffer:
        buffer.write(arquivo.file.read())

    doc = DocumentoProfissional(
        profissional_id=id,
        caminho=str(destino),
        tipo=tipo,
        valido=False
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return {"msg": "Documento armazenado", "doc_id": doc.id, "arquivo": str(destino)}

@router.patch("/{id}/documentos/{doc_id}/validar")
async def validar_documento(
    id: int,
    doc_id: int,
    valido: bool = True,
    db: Session = Depends(get_db)
):
    profissional = db.query(Professional).filter_by(id=id).first()
    if not profissional:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")

    documento = db.query(DocumentoProfissional).filter_by(id=doc_id, profissional_id=id).first()
    if not documento:
        raise HTTPException(status_code=404, detail="Documento não encontrado")

    documento.valido = valido
    db.commit()
    db.refresh(documento)

    # 🔐 Verifica se há dois ou mais documentos válidos
    docs_validos = db.query(DocumentoProfissional).filter_by(profissional_id=id, valido=True).count()
    if docs_validos >= 1:  # ✅ Ajuste aqui para 1 caso use apenas CNH
        try:
            # ✅ Verifica se profissional tem 'phone' antes de enviar
            if profissional.phone:
                await send_text_v2(profissional.phone, "✅ CNH validada! Digite *online* para começar a receber serviços.")
                await set_state(profissional.phone, "APROVADO")
        except Exception as e:
            print(f"[⚠️ WhatsApp] Falha ao notificar profissional: {e}")

    return {
        "msg": "Documento validado com sucesso" if valido else "Documento marcado como inválido",
        "doc_id": doc_id,
        "valido": documento.valido
    }
