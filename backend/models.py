# backend/models.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Agent(Base):
    __tablename__ = "agents"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    tech_skill = Column(Float, default=0.0)
    billing_skill = Column(Float, default=0.0)
    legal_skill = Column(Float, default=0.0)
    current_load = Column(Integer, default=0)
    tickets = relationship("Ticket", back_populates="agent")

class Incident(Base):
    __tablename__ = "incidents"
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="Open")
    tickets = relationship("Ticket", back_populates="incident")

class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(Integer, primary_key=True, index=True)
    payload = Column(String)
    category = Column(String, nullable=True)
    urgency_score = Column(Float, nullable=True)
    status = Column(String, default="Pending")
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=True)
    
    agent = relationship("Agent", back_populates="tickets")
    incident = relationship("Incident", back_populates="tickets")