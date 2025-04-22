from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database.database import Base

class Professional(Base):
    __tablename__ = "professionals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    cpf = Column(String, unique=True, nullable=False)
    phone = Column(String, unique=True)
    is_available = Column(Boolean, default=True)
    rating = Column(Float, default=4.5)
    total_atendimentos = Column(Integer, default=0)
    ultimo_aceite = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    services = relationship("ServiceRequest", back_populates="professional")
    documentos = relationship("DocumentoProfissional", back_populates="profissional", cascade="all, delete-orphan")

class DocumentoProfissional(Base):
    __tablename__ = "documentos_profissionais"

    id = Column(Integer, primary_key=True, index=True)
    profissional_id = Column(Integer, ForeignKey("professionals.id"), nullable=False)
    caminho = Column(String, nullable=False)
    tipo = Column(String, nullable=True)
    data_envio = Column(DateTime, default=datetime.utcnow)
    valido = Column(Boolean, default=False)

    profissional = relationship("Professional", back_populates="documentos")