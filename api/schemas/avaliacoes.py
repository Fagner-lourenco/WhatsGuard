from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AvaliacaoCreate(BaseModel):
    profissional_id: int = Field(..., example=1)
    solicitacao_id: int = Field(..., example=3)
    nota: float = Field(..., ge=0, le=5)
    comentario: Optional[str] = Field(None, example="Profissional muito eficiente e pontual")


class AvaliacaoOut(BaseModel):
    id: int
    profissional_id: int
    solicitacao_id: int
    nota: float
    comentario: Optional[str]
    criado_em: datetime

    class Config:
        from_attributes = True


class AvaliacaoClienteCreate(BaseModel):
    client_id: int
    profissional_id: int
    nota: float = Field(..., ge=0, le=5)
    comentario: Optional[str]


class AvaliacaoClienteOut(BaseModel):
    id: int
    client_id: int
    profissional_id: int
    nota: float
    comentario: Optional[str]
    criado_em: datetime

    class Config:
        from_attributes = True
