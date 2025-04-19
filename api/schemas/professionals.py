from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProfessionalCreate(BaseModel):
    name: str

class ProfessionalOut(BaseModel):
    id: int
    name: str
    is_available: bool
    rating: float
    total_atendimentos: int
    ultimo_aceite: Optional[datetime]

    class Config:
        from_attributes = True

class AvaliacaoInput(BaseModel):
    nova_nota: float


class ProfessionalAccept(BaseModel):
    professional_id: int
    solicitacao_id: int
