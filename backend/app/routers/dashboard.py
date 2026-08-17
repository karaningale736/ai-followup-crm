from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.enums import ClientStage, AgreementStatus
from app.models.client import Client
from app.models.meeting import Meeting
from app.models.agreement import Agreement
from app.services.followup_engine import analyze
from app.routers.followups import _snapshot_from_client

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def dashboard(db: Session = Depends(get_db)):
    clients = db.query(Client).all()

    due_today = 0
    overdue = 0
    high_priority = 0
    for c in clients:
        decision = analyze(_snapshot_from_client(c))
        if decision.is_due:
            due_today += 1
            if decision.priority.value == "HIGH":
                overdue += 1
        if c.priority.value == "HIGH":
            high_priority += 1

    meetings_today = (
        db.query(Meeting).filter(Meeting.meeting_date == date.today()).count()
    )
    agreements_pending = db.query(Agreement).filter(
        Agreement.status.in_([AgreementStatus.SENT, AgreementStatus.PENDING_SIGNATURE])
    ).count()
    agreements_opened = db.query(Agreement).filter(Agreement.status == AgreementStatus.OPENED).count()
    agreements_signed = db.query(Agreement).filter(Agreement.status == AgreementStatus.SIGNED).count()
    declined = db.query(Client).filter(Client.current_stage == ClientStage.DECLINED).count()

    return {
        "total_clients": len(clients),
        "followups_due_today": due_today,
        "overdue_followups": overdue,
        "meetings_today": meetings_today,
        "agreements_pending": agreements_pending,
        "agreements_opened": agreements_opened,
        "agreements_signed": agreements_signed,
        "declined_clients": declined,
        "high_priority_clients": high_priority,
    }
