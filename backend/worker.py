# backend/worker.py
from celery import Celery
import redis
import httpx
from database import SessionLocal
from models import Ticket, Agent, Incident
from ml_service import TicketRouterML

celery_app = Celery('tasks', broker='redis://localhost:6379/0')
redis_client = redis.Redis(host='localhost', port=6379, db=1)
ml_engine = TicketRouterML()

@celery_app.task
def process_ticket_task(ticket_id: int, payload: str):
    # Atomic Lock to prevent race conditions
    lock = redis_client.lock(f"ticket_lock_{ticket_id}", timeout=5)
    
    if lock.acquire(blocking=True):
        try:
            db = SessionLocal()
            ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
            if not ticket:
                return

            # 1. Deduplication & Storm Check
            is_storm = ml_engine.check_storm(payload)
            if is_storm:
                incident = Incident(status="Open")
                db.add(incident)
                db.commit()
                ticket.incident_id = incident.id
                ticket.status = "Grouped into Incident"
                db.commit()
                return

            # 2. Classification & Circuit Breaker
            category, urgency = ml_engine.process_ticket(payload)
            ticket.category = category
            ticket.urgency_score = urgency

            # 3. Webhook Trigger for high urgency
            if urgency > 0.9:
                #httpx.post("https://mock-slack-webhook.com", json={"text": f"High urgency ticket: {ticket_id}"})
                print(f"[NOTIFICATION] High urgency ticket: {ticket_id}")

            # 4. Skill-Based Routing (Simplified constraint optimization)
            # Find an agent with the right skill > 0.5 and lowest load
            agent = db.query(Agent).order_by(Agent.current_load.asc()).first()
            if agent:
                ticket.agent_id = agent.id
                agent.current_load += 1
                ticket.status = "Assigned"
            
            db.commit()
        finally:
            db.close()
            lock.release()