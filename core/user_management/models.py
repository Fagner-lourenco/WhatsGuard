from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from core.database.database import Base

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=True)
    telefone = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)