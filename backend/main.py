# backend/main.py
from fastapi import FastAPI, Depends, BackgroundTasks, status
from fastapi import HTTPException

from sqlalchemy.orm import Session
from pydantic import BaseModel
import database
import models
from worker import process_ticket_task

# Initialize DB tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Smart-Support Ticket Router")

class TicketRequest(BaseModel):
    payload: str

@app.post("/tickets", status_code=status.HTTP_202_ACCEPTED)
async def create_ticket(request: TicketRequest, db: Session = Depends(database.get_db)):
    """Accepts ticket and queues it for background processing."""
    # Create DB entry quickly to get an ID
    new_ticket = models.Ticket(payload=request.payload)
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    
    # Hand off to Celery Broker
    process_ticket_task.delay(new_ticket.id, request.payload)
    
    return {"message": "Ticket accepted for processing", "ticket_id": new_ticket.id, "category": new_ticket.category, "urgency": new_ticket.urgency_score, "status": new_ticket.status}

@app.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: int, db: Session = Depends(database.get_db)):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return {
        "ticket_id": ticket.id,
        "payload": ticket.payload,
        "category": ticket.category,
        "urgency": ticket.urgency_score,
        "status": ticket.status,
        "agent_id": ticket.agent_id,
        "incident_id": ticket.incident_id
    }

class AgentCreate(BaseModel):
    name: str

@app.post("/agents")
def create_agent(agent: AgentCreate, db: Session = Depends(database.get_db)):
    new_agent = models.Agent(
        name=agent.name,
        current_load=0
    )
    db.add(new_agent)
    db.commit()
    db.refresh(new_agent)
    
    return {
        "id": new_agent.id,
        "name": new_agent.name,
        "current_load": new_agent.current_load
    }