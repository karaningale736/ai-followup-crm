from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.models.client import Client
from app.services.ai_provider import get_ai_provider

router = APIRouter(prefix="/api/responses", tags=["responses"])


class ClassifyRequest(BaseModel):
    client_id: int
    message_text: str


class ClassifyResponse(BaseModel):
    classification: str
    confidence: float
    recommended_stage: str | None
    recommended_action: str
    reason: str


@router.post("/classify", response_model=ClassifyResponse)
def classify_response(payload: ClassifyRequest, db: Session = Depends(get_db)):
    client = db.get(Client, payload.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    ai = get_ai_provider()
    result = ai.classify_response(
        payload.message_text,
        {"stage": client.current_stage.value, "client_concern": client.client_concern},
    )
    # NOTE: this endpoint only recommends. Applying `recommended_stage` to the
    # client record requires a separate, explicit PUT /api/clients/{id} call --
    # the AI never silently mutates CRM state, per spec section 29.
    return result
