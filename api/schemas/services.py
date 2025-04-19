from pydantic import BaseModel
from typing import Optional

class ServiceRequestCreate(BaseModel):
    client_id: int
    location: str

class ServiceRequestOut(BaseModel):
    id: int
    client_id: int
    location: str
    status: str
    price: Optional[float] = None  # <- Correção feita aqui

    class Config:
        from_attributes = True

class PrecoEstimadoRequest(BaseModel):
    profissional_id: int
    location: str

class PrecoEstimadoOut(BaseModel):
    preco_estimado: float
