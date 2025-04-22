# api/schemas/professionals.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ProfessionalCreate(BaseModel):
    name: str = Field(..., example="João da Silva")
    cpf: str = Field(..., example="123.456.789-00", min_length=11, max_length=14)
    phone: str

class ProfessionalOut(BaseModel):
    id: int
    name: str
    cpf: str
    phone: Optional[str]
    rating: float
    total_atendimentos: int
    is_available: bool
    ultimo_aceite: Optional[datetime] = None

    class Config:
        orm_mode = True

class AvaliacaoInput(BaseModel):
    nova_nota: float = Field(..., ge=0, le=5, example=4.5)

class ProfessionalAccept(BaseModel):
    professional_id: int = Field(..., example=2)
    solicitacao_id: int = Field(..., example=7)
