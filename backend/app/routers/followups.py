from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.enums import ClientStage
from app.models.client import Client
from app.models.template import Template
from app.schemas.followup import (
    AnalyzeRequest, AnalyzeResponse, GenerateEmailRequest, GenerateEmailResponse,
)
from app.services.followup_engine import analyze, ClientSnapshot
from app.services.ai_provider import get_ai_provider

router = APIRouter(prefix="/api/followups", tags=["followups"])


def _snapshot_from_client(client: Client) -> ClientSnapshot:
    latest_agreement = client.agreements[-1] if client.agreements else None
    latest_meeting = client.meetings[-1] if client.meetings else None

    return ClientSnapshot(
        stage=client.current_stage,
        last_contact_date=client.last_contact_date,
        last_email_sent_date=client.last_email_sent_date,
        followup_count=client.followup_count,
        agreement_status=latest_agreement.status.value if latest_agreement else "NOT_SENT",
        agreement_sent_at=latest_agreement.sent_at if latest_agreement else None,
        agreement_opened_at=latest_agreement.opened_at if latest_agreement else None,
        meeting_status=latest_meeting.status.value if latest_meeting else None,
        meeting_date=latest_meeting.meeting_date if latest_meeting else None,
        client_concern=client.client_concern,
        has_approved_offer=client.offer_amount is not None,
    )


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_client(payload: AnalyzeRequest, db: Session = Depends(get_db)):
    client = db.get(Client, payload.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    decision = analyze(_snapshot_from_client(client))
    return AnalyzeResponse(
        client_id=client.id,
        current_stage=client.current_stage.value,
        is_due=decision.is_due,
        recommended_action=decision.recommended_action,
        template_category=decision.template_category.value if decision.template_category else None,
        tone=decision.tone.value,
        priority=decision.priority.value,
        reason=decision.reason,
        days_since_last_contact=decision.days_since_last_contact,
        days_since_agreement_sent=decision.days_since_agreement_sent,
        days_since_agreement_opened=decision.days_since_agreement_opened,
    )


@router.post("/generate", response_model=GenerateEmailResponse)
def generate_email(payload: GenerateEmailRequest, db: Session = Depends(get_db)):
    client = db.get(Client, payload.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    decision = analyze(_snapshot_from_client(client))

    template = None
    if payload.template_id:
        template = db.get(Template, payload.template_id)
    elif decision.template_category:
        template = (
            db.query(Template)
            .filter(Template.category == decision.template_category, Template.active.is_(True))
            .first()
        )

    if not template:
        raise HTTPException(
            status_code=422,
            detail="No matching active template found for this client's recommended category. "
                   "Create/activate one in Template Management first.",
        )

    variables = {
        "client_first_name": client.first_name,
        "client_full_name": client.full_name,
        "company_name": client.company_name,
        "feature_title": client.feature_title,
        "edition_title": client.edition_title,
        "assigned_manager": client.assigned_manager,
        "offer_amount": client.offer_amount,
        "currency": client.currency,
        **payload.additional_variables,
    }

    ai = get_ai_provider()
    result = ai.personalize_email({
        "template_subject": template.subject,
        "template_body": template.body,
        "variables": variables,
        "client_concern": client.client_concern,
        "stage": client.current_stage.value,
    })

    return GenerateEmailResponse(
        client_id=client.id,
        template_id=template.id,
        subject=result["subject"],
        email_body=result["email_body"],
        cta=result["cta"],
        tone=decision.tone.value,
        template_category=decision.template_category.value if decision.template_category else None,
    )


@router.get("/due")
def followups_due(db: Session = Depends(get_db)):
    clients = db.query(Client).all()
    due = []
    for c in clients:
        decision = analyze(_snapshot_from_client(c))
        if decision.is_due:
            due.append({
                "client_id": c.id,
                "client_name": c.full_name,
                "company_name": c.company_name,
                "stage": c.current_stage.value,
                "priority": decision.priority.value,
                "recommended_action": decision.recommended_action,
                "days_since_last_contact": decision.days_since_last_contact,
            })
    return due


@router.get("/overdue")
def followups_overdue(db: Session = Depends(get_db)):
    """Subset of 'due' where the client has waited notably longer than the
    recommended window (HIGH priority is used as the overdue signal)."""
    return [item for item in followups_due(db) if item["priority"] == "HIGH"]
