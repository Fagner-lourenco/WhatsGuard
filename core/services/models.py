from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Enum, Text, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum
from core.database.database import Base

class StatusEnum(PyEnum):
    pendente = "pendente"
    aceito = "aceito"
    finalizado = "finalizado"

class ServiceRequest(Base):
    __tablename__ = "service_requests"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    professional_id = Column(Integer, ForeignKey("professionals.id"), nullable=True)

    location = Column(String, nullable=False)
    scheduled_datetime = Column(DateTime, nullable=True)
    service_type = Column(String, nullable=False)
    agent_count = Column(Integer, nullable=False)
    duration_hours = Column(Integer, nullable=False)
    attire = Column(String, nullable=False)
    equipments = Column(ARRAY(String), nullable=True)

    status = Column(Enum(StatusEnum), default=StatusEnum.pendente)
    price = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    accepted_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    client = relationship("Client")
    professional = relationship("Professional", back_populates="services")
    avaliacoes = relationship("Avaliacao", back_populates="solicitacao")

class Avaliacao(Base):
    __tablename__ = "avaliacoes"

    id = Column(Integer, primary_key=True, index=True)
    profissional_id = Column(Integer, ForeignKey("professionals.id"), nullable=False)
    solicitacao_id = Column(Integer, ForeignKey("service_requests.id"), nullable=False)
    nota = Column(Float, nullable=False)
    comentario = Column(Text, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    profissional = relationship("Professional")
    solicitacao = relationship("ServiceRequest", back_populates="avaliacoes")

class AvaliacaoCliente(Base):
    __tablename__ = "avaliacoes_cliente"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    profissional_id = Column(Integer, ForeignKey("professionals.id"), nullable=False)
    nota = Column(Float, nullable=False)
    comentario = Column(Text, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    client = relationship("Client")
    profissional = relationship("Professional")