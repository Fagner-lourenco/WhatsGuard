from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime
from core.database.database import Base
from datetime import datetime

class Professional(Base):
    __tablename__ = "professionals"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    is_available = Column(Boolean, default=True)
    rating = Column(Float, default=4.5)
    total_atendimentos = Column(Integer, default=0)
    ultimo_aceite = Column(DateTime, nullable=True, default=None)  # 👈 NOVO!
