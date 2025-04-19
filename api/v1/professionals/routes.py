from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from core.database.database import SessionLocal
from core.professionals.models import Professional
from api.schemas.professionals import ProfessionalCreate, ProfessionalOut, AvaliacaoInput, ProfessionalAccept
from datetime import datetime

router = APIRouter(prefix="/profissionais", tags=["Profissionais"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=ProfessionalOut)
def criar_profissional(prof: ProfessionalCreate, db: Session = Depends(get_db)):
    novo = Professional(
        name=prof.name,
        is_available=True,
        rating=4.5,
        total_atendimentos=0
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo

@router.get("/", response_model=list[ProfessionalOut])
def listar_profissionais(db: Session = Depends(get_db)):
    return db.query(Professional).all()

@router.patch("/{id}/avaliar")
def avaliar_profissional(id: int, entrada: AvaliacaoInput, db: Session = Depends(get_db)):
    profissional = db.query(Professional).filter_by(id=id).first()
    if not profissional:
        raise HTTPException(status_code=404, detail="Profissional nao encontrado")

    profissional.rating = (profissional.rating + entrada.nova_nota) / 2
    db.commit()
    return {"msg": f"Nova média: {profissional.rating:.2f}"}

@router.get("/ranking", response_model=list[ProfessionalOut])
def ranking_profissionais(db: Session = Depends(get_db)):
    return db.query(Professional).order_by(Professional.rating.desc(), Professional.total_atendimentos.desc()).all()
