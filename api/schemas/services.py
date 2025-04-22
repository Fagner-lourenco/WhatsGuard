# api/schemas/services.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from core.services.models import StatusEnum

class ServiceRequestCreate(BaseModel):
    client_id: int
    location: str
    scheduled_datetime: datetime
    service_type: str
    agent_count: int
    duration_hours: int
    attire: str
    equipments: Optional[List[str]] = Field(default=[])

class ServiceRequestOut(BaseModel):
    id: int
    client_id: int
    location: str
    scheduled_datetime: datetime
    service_type: str
    agent_count: int
    duration_hours: int
    attire: str
    equipments: Optional[List[str]]
    status: StatusEnum
    price: Optional[float]
    created_at: datetime
    accepted_at: Optional[datetime]
    finished_at: Optional[datetime]
    professional_id: Optional[int]

    class Config:
        from_attributes = True

class PrecoEstimadoRequest(BaseModel):
    profissional_id: int = Field(..., example=2)
    location: str = Field(..., example="Rua das Laranjeiras, 456")

class PrecoEstimadoOut(BaseModel):
    preco_estimado: float = Field(..., example=89.90)
