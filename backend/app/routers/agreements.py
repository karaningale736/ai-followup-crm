from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.enums import AgreementStatus, ClientStage
from app.models.agreement import Agreement
from app.models.client import Client

router = APIRouter(prefix="/api/agreements", tags=["agreements"])


class AgreementIn(BaseModel):
    client_id: int
    agreement_url: str = ""
    status: AgreementStatus = AgreementStatus.NOT_SENT
    notes: str = ""


class AgreementUpdate(BaseModel):
    status: Optional[AgreementStatus] = None
    notes: Optional[str] = None


class AgreementOut(BaseModel):
    id: int
    client_id: int
    agreement_url: str
    status: str
    sent_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    signed_at: Optional[datetime] = None
    declined_at: Optional[datetime] = None
    notes: str

    class Config:
        from_attributes = True


# Mirrors the stage each agreement status should push the client toward.
STATUS_TO_STAGE = {
    AgreementStatus.SENT: ClientStage.AGREEMENT_SENT,
    AgreementStatus.OPENED: ClientStage.AGREEMENT_OPENED,
    AgreementStatus.PENDING_SIGNATURE: ClientStage.AGREEMENT_PENDING_SIGNATURE,
    AgreementStatus.SIGNED: ClientStage.SIGNED,
    AgreementStatus.DECLINED: ClientStage.DECLINED,
}


@router.post("", response_model=AgreementOut)
def create_agreement(payload: AgreementIn, db: Session = Depends(get_db)):
    client = db.get(Client, payload.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    agreement = Agreement(**payload.model_dump())
    if payload.status == AgreementStatus.SENT:
        agreement.sent_at = datetime.utcnow()
    db.add(agreement)

    if payload.status in STATUS_TO_STAGE:
        client.current_stage = STATUS_TO_STAGE[payload.status]

    db.commit()
    db.refresh(agreement)
    return agreement


@router.get("", response_model=List[AgreementOut])
def list_agreements(db: Session = Depends(get_db), client_id: Optional[int] = None,
                     status: Optional[AgreementStatus] = None):
    q = db.query(Agreement)
    if client_id:
        q = q.filter(Agreement.client_id == client_id)
    if status:
        q = q.filter(Agreement.status == status)
    return q.all()


@router.put("/{agreement_id}", response_model=AgreementOut)
def update_agreement(agreement_id: int, payload: AgreementUpdate, db: Session = Depends(get_db)):
    agreement = db.get(Agreement, agreement_id)
    if not agreement:
        raise HTTPException(status_code=404, detail="Agreement not found")

    if payload.notes is not None:
        agreement.notes = payload.notes

    if payload.status is not None and payload.status != agreement.status:
        now = datetime.utcnow()
        agreement.status = payload.status
        if payload.status == AgreementStatus.SENT:
            agreement.sent_at = now
        elif payload.status == AgreementStatus.OPENED:
            agreement.opened_at = now
        elif payload.status == AgreementStatus.SIGNED:
            agreement.signed_at = now
        elif payload.status == AgreementStatus.DECLINED:
            agreement.declined_at = now

        client = db.get(Client, agreement.client_id)
        if client and payload.status in STATUS_TO_STAGE:
            client.current_stage = STATUS_TO_STAGE[payload.status]

    db.commit()
    db.refresh(agreement)
    return agreement
