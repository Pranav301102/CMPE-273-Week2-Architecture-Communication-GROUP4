from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="NotificationService (Sync REST)")

class SendIn(BaseModel):
    order_id: str
    user_id: str
    message: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/send")
def send(req: SendIn):
    # In real system: email/sms/push
    return {"status": "sent", "order_id": req.order_id}