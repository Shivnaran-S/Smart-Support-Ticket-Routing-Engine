POST /tickets
↓
FastAPI saves ticket
↓
.delay() sends task to Redis
↓
Celery worker picks task
↓
Worker updates DB
