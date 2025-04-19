from sqlalchemy import Column, Integer, String, ForeignKey, DateTime 
from sqlalchemy.orm import relationship 
from core.database.database import Base 
from datetime import datetime 
 
class ServiceRequest(Base): 
    __tablename__ = "service_requests" 
    id = Column(Integer, primary_key=True, index=True) 
    client_id = Column(Integer, nullable=False) 
    location = Column(String, nullable=False) 
    status = Column(String, default="pendente") 
    created_at = Column(DateTime, default=datetime.utcnow) 
