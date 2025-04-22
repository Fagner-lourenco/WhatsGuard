# api/schemas/clients.py
from pydantic import BaseModel, Field
from typing import Optional

class ClientCreate(BaseModel):
    nome: str = Field(..., example="João da Silva")
    telefone: str = Field(..., example="+554199999999")
    email: Optional[str] = Field(None, example="joao@email.com")

class ClientOut(BaseModel):
    id: int
    nome: str
    telefone: str
    email: Optional[str]

    class Config:
        from_attributes = True
