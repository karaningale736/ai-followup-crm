import os
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.enums import EmailDirection, EmailStatus
from app.models.client import Client
from app.models.email_history import EmailHistory
from app.services.followup_engine import analyze
from app.routers.followups import _snapshot_from_client
from app.services import inbox_monitor

router = APIRouter(prefix="/api/emails", tags=["emails"])


class EmailDraftIn(BaseModel):
    client_id: int
    subject: str
    body: str
    template_id: Optional[int] = None


class EmailSendIn(EmailDraftIn):
    force_mock: bool = False


class InboxSyncIn(BaseModel):
    imap_host: Optional[str] = None
    imap_port: int = 993
    username: Optional[str] = None
    password: Optional[str] = None
    mailbox: str = "INBOX"
    use_ssl: bool = True


class EmailOut(BaseModel):
    id: int
    client_id: int
    direction: str
    subject: str
    body: str
    status: str
    sent_at: Optional[datetime] = None

    class Config:
        from_attributes = True


@router.post("/draft", response_model=EmailOut)
def save_draft(payload: EmailDraftIn, db: Session = Depends(get_db)):
    client = db.get(Client, payload.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    record = EmailHistory(
        client_id=client.id,
        direction=EmailDirection.OUTBOUND,
        subject=payload.subject,
        body=payload.body,
        template_id=payload.template_id,
        stage=client.current_stage,
        status=EmailStatus.DRAFT,
        sender=os.getenv("SMTP_FROM_EMAIL", "drafts@company.local"),
        recipient=client.email,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.post("/send", response_model=EmailOut)
def send_email(payload: EmailSendIn, db: Session = Depends(get_db)):
    """
    Sends (or mock-sends) an already-reviewed email and updates the client's
    contact tracking fields. This endpoint represents the explicit human
    confirmation step -- nothing upstream auto-sends without hitting this.
    """
    client = db.get(Client, payload.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    smtp_host = os.getenv("SMTP_HOST")
    from_email = os.getenv("SMTP_FROM_EMAIL", "noreply@company.local")

    status = EmailStatus.MOCK_SENT
    if smtp_host and not payload.force_mock:
        try:
            msg = MIMEText(payload.body)
            msg["Subject"] = payload.subject
            msg["From"] = from_email
            msg["To"] = client.email
            with smtplib.SMTP(smtp_host, int(os.getenv("SMTP_PORT", "587"))) as server:
                server.starttls()
                server.login(os.getenv("SMTP_USERNAME", ""), os.getenv("SMTP_PASSWORD", ""))
                server.sendmail(from_email, [client.email], msg.as_string())
            status = EmailStatus.SENT
        except Exception:
            status = EmailStatus.FAILED

    now = datetime.utcnow()
    record = EmailHistory(
        client_id=client.id,
        direction=EmailDirection.OUTBOUND,
        subject=payload.subject,
        body=payload.body,
        template_id=payload.template_id,
        stage=client.current_stage,
        status=status,
        sender=from_email,
        recipient=client.email,
        sent_at=now,
    )
    db.add(record)

    if status in (EmailStatus.SENT, EmailStatus.MOCK_SENT):
        client.last_contact_date = now
        client.last_email_sent_date = now
        client.followup_count += 1
        decision = analyze(_snapshot_from_client(client))
        client.priority = decision.priority

    db.commit()
    db.refresh(record)
    return record


@router.get("/history/{client_id}", response_model=List[EmailOut])
def email_history(client_id: int, db: Session = Depends(get_db)):
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return (
        db.query(EmailHistory)
        .filter(EmailHistory.client_id == client_id)
        .order_by(EmailHistory.created_at.desc())
        .all()
    )


@router.post("/inbox/sync", response_model=List[EmailOut])
def sync_inbox(payload: InboxSyncIn, db: Session = Depends(get_db)):
    messages = inbox_monitor.fetch_incoming_messages({
        "imap_host": payload.imap_host or os.getenv("IMAP_HOST"),
        "imap_port": payload.imap_port or int(os.getenv("IMAP_PORT", "993")),
        "username": payload.username or os.getenv("IMAP_USERNAME"),
        "password": payload.password or os.getenv("IMAP_PASSWORD"),
        "mailbox": payload.mailbox or os.getenv("IMAP_MAILBOX", "INBOX"),
        "use_ssl": payload.use_ssl if payload.use_ssl is not None else str(os.getenv("IMAP_USE_SSL", "true")).lower() in {"1", "true", "yes", "on"},
    })

    records: List[EmailOut] = []
    for message in messages:
        sender_email = (getattr(message, "from_email", "") or "").lower()
        client = db.query(Client).filter(Client.email.ilike(sender_email)).first()
        if not client:
            client = db.query(Client).filter(Client.email.ilike(f"%{sender_email.split('@')[0]}%" )).first()

        client_id = client.id if client else None
        record = EmailHistory(
            client_id=client_id if client_id is not None else 0,
            direction=EmailDirection.INBOUND,
            subject=getattr(message, "subject", "") or "No subject",
            body=getattr(message, "body", "") or "",
            status=EmailStatus.REPLY_REQUIRED,
            sender=getattr(message, "from_email", "") or "unknown@unknown.local",
            recipient=os.getenv("IMAP_USERNAME") or os.getenv("SMTP_FROM_EMAIL") or "inbox@company.local",
            message_id=getattr(message, "message_id", "") or "",
            received_at=getattr(message, "received_at", None) or datetime.utcnow(),
            stage=client.current_stage if client else None,
        )

        if client:
            client.last_email_received_date = record.received_at
            client.last_contact_date = record.received_at
            client.priority = analyze(_snapshot_from_client(client)).priority

        db.add(record)
        db.commit()
        db.refresh(record)
        records.append(record)

    return records


@router.get("/inbox/notifications", response_model=List[EmailOut])
def inbox_notifications(db: Session = Depends(get_db)):
    return (
        db.query(EmailHistory)
        .filter(EmailHistory.direction == EmailDirection.INBOUND)
        .filter(EmailHistory.status == EmailStatus.REPLY_REQUIRED)
        .order_by(EmailHistory.received_at.desc())
        .all()
    )
