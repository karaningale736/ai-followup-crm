"""
followup_engine.py

Deterministic business logic for follow-up timing, per the supplied
business workflow. This module makes NO AI calls and has NO knowledge of
templates' text content -- it only decides WHETHER a follow-up is due,
WHICH category of follow-up/template applies, what TONE to use, and what
PRIORITY to assign. AI personalization happens downstream in
ai_email_generator.py, after this engine has already decided the facts.

Working-day windows straight from the business workflow:
    Follow-Up 1: 2-3 working days after first contact, same subject line
    Follow-Up 2: 3-4 working days after Follow-Up 1, same subject line
    Follow-Up 3: 4-6 working days after Follow-Up 2, NEW subject line
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, Set

from app.core.enums import ClientStage, Tone, Priority, TemplateCategory, TERMINAL_STAGES
from app.core.workdays import working_days_since


# Minimum working days elapsed before each follow-up becomes "due".
# (min, max) is informational for the UI; `min` drives the is_due check.
FOLLOWUP_WINDOWS = {
    1: (2, 3),
    2: (3, 4),
    3: (4, 6),
}

# Stages that are still in the pre-closing follow-up sequence.
PRE_CLOSING_STAGES = {
    ClientStage.NEW_LEAD,
    ClientStage.INITIAL_FOLLOW_UP,
    ClientStage.FOLLOW_UP_2,
    ClientStage.FOLLOW_UP_3,
}


@dataclass
class ClientSnapshot:
    """Minimal input the engine needs -- decoupled from the ORM model so it's
    easy to unit test without a database."""
    stage: ClientStage
    last_contact_date: Optional[datetime] = None
    last_email_sent_date: Optional[datetime] = None
    followup_count: int = 0

    agreement_status: Optional[str] = None  # NOT_SENT/SENT/OPENED/PENDING_SIGNATURE/SIGNED/DECLINED
    agreement_sent_at: Optional[datetime] = None
    agreement_opened_at: Optional[datetime] = None

    meeting_status: Optional[str] = None
    meeting_date: Optional[date] = None

    client_concern: str = ""
    has_approved_offer: bool = False

    holidays: Set[date] = field(default_factory=set)


@dataclass
class FollowUpDecision:
    is_due: bool
    recommended_action: str
    template_category: Optional[TemplateCategory]
    tone: Tone
    priority: Priority
    reason: str
    next_followup_date: Optional[date] = None
    days_since_last_contact: Optional[int] = None
    days_since_agreement_sent: Optional[int] = None
    days_since_agreement_opened: Optional[int] = None


def _days_since(dt: Optional[datetime], holidays: Set[date]) -> Optional[int]:
    if dt is None:
        return None
    return working_days_since(dt, holidays)


def analyze(client: ClientSnapshot, today: Optional[date] = None) -> FollowUpDecision:
    """
    Core decision function. Pure and deterministic -- same input always
    produces the same output, no AI involved.
    """
    holidays = client.holidays or set()

    days_since_contact = _days_since(client.last_contact_date, holidays)
    days_since_agreement_sent = _days_since(client.agreement_sent_at, holidays)
    days_since_agreement_opened = _days_since(client.agreement_opened_at, holidays)

    # 1. Terminal stages: never recommend a follow-up.
    if client.stage in TERMINAL_STAGES:
        return FollowUpDecision(
            is_due=False,
            recommended_action="No action -- client is in a terminal stage.",
            template_category=None,
            tone=Tone.POLITE_PROFESSIONAL,
            priority=Priority.LOW,
            reason=f"Stage '{client.stage.value}' is terminal; automation stops here.",
            days_since_last_contact=days_since_contact,
            days_since_agreement_sent=days_since_agreement_sent,
            days_since_agreement_opened=days_since_agreement_opened,
        )

    # 2. Budget objection -- needs a human-approved offer, AI must never invent one.
    if client.stage == ClientStage.BUDGET_OBJECTION:
        if client.has_approved_offer:
            return FollowUpDecision(
                is_due=True,
                recommended_action="Discuss the approved special offer with the client.",
                template_category=TemplateCategory.SPECIAL_OFFER,
                tone=Tone.FRIENDLY_ENGAGING,
                priority=Priority.HIGH,
                reason="Budget objection with an approved offer on file -- ready to present it.",
                days_since_last_contact=days_since_contact,
            )
        return FollowUpDecision(
            is_due=False,
            recommended_action="Waiting on manager-approved offer before contacting client.",
            template_category=TemplateCategory.BUDGET_OBJECTION,
            tone=Tone.POLITE_PROFESSIONAL,
            priority=Priority.MEDIUM,
            reason="Budget concern raised, but no approved offer has been entered yet.",
            days_since_last_contact=days_since_contact,
        )

    # 3. Agreement-stage logic takes priority once an agreement has been sent.
    if client.agreement_status in ("SENT", "OPENED", "PENDING_SIGNATURE"):
        return _agreement_decision(client, days_since_contact, days_since_agreement_sent,
                                    days_since_agreement_opened)

    # 4. Meeting-stage logic.
    if client.stage in (ClientStage.MEETING_REQUESTED, ClientStage.MEETING_SCHEDULED,
                        ClientStage.MEETING_CONFIRMED):
        return _meeting_decision(client, days_since_contact)

    # 5. Participation pending.
    if client.stage == ClientStage.PARTICIPATION_PENDING:
        is_due = days_since_contact is not None and days_since_contact >= 2
        return FollowUpDecision(
            is_due=is_due,
            recommended_action="Request participation confirmation." if is_due else "Wait for client response.",
            template_category=TemplateCategory.PARTICIPATION_CONFIRMATION,
            tone=Tone.ACTION_ORIENTED,
            priority=Priority.MEDIUM if is_due else Priority.LOW,
            reason="Participation confirmation pending" + (
                f", {days_since_contact} working day(s) since last contact." if days_since_contact else "."
            ),
            days_since_last_contact=days_since_contact,
        )

    # 6. Standard pre-closing follow-up sequence (1 -> 2 -> 3).
    if client.stage in PRE_CLOSING_STAGES:
        return _pre_closing_decision(client, days_since_contact)

    # 7. Fallback -- stage not covered by a specific rule (e.g. INTERESTED,
    # VIRTUAL_PARTICIPATION, PAYMENT_DISCUSSION): recommend a check-in once
    # a reasonable amount of time has passed, no aggressive default.
    is_due = days_since_contact is not None and days_since_contact >= 3
    return FollowUpDecision(
        is_due=is_due,
        recommended_action="Send a check-in follow-up." if is_due else "No action needed yet.",
        template_category=TemplateCategory.OTHER_APPROVED_TEMPLATE,
        tone=Tone.FRIENDLY_ENGAGING,
        priority=Priority.MEDIUM if is_due else Priority.LOW,
        reason=f"Stage '{client.stage.value}' has no dedicated rule; using general check-in threshold.",
        days_since_last_contact=days_since_contact,
    )


def _pre_closing_decision(client: ClientSnapshot, days_since_contact: Optional[int]) -> FollowUpDecision:
    # followup_count 0 -> about to send Follow-Up 1, etc.
    next_number = min(client.followup_count + 1, 3)
    min_days, max_days = FOLLOWUP_WINDOWS[next_number]

    is_due = days_since_contact is not None and days_since_contact >= min_days

    category = {
        1: TemplateCategory.FOLLOW_UP_1,
        2: TemplateCategory.FOLLOW_UP_2,
        3: TemplateCategory.FOLLOW_UP_3,
    }[next_number]

    subject_note = "keep the existing subject line" if next_number < 3 else "use a NEW subject line"

    priority = Priority.LOW
    if is_due:
        priority = Priority.HIGH if (days_since_contact and days_since_contact > max_days) else Priority.MEDIUM

    return FollowUpDecision(
        is_due=is_due,
        recommended_action=f"Send Follow-Up {next_number} ({subject_note})." if is_due else "No follow-up due yet.",
        template_category=category,
        tone=Tone.POLITE_PROFESSIONAL if next_number == 1 else Tone.FRIENDLY_ENGAGING,
        priority=priority,
        reason=(
            f"Follow-Up {next_number} window is {min_days}-{max_days} working days; "
            f"{days_since_contact if days_since_contact is not None else 'unknown'} have elapsed."
        ),
        days_since_last_contact=days_since_contact,
    )


def _agreement_decision(
    client: ClientSnapshot,
    days_since_contact: Optional[int],
    days_since_agreement_sent: Optional[int],
    days_since_agreement_opened: Optional[int],
) -> FollowUpDecision:
    if client.agreement_status == "OPENED":
        # "Agreement Opened - Signature Pending"
        is_due = days_since_agreement_opened is not None and days_since_agreement_opened >= 2
        priority = Priority.HIGH if is_due else Priority.MEDIUM
        return FollowUpDecision(
            is_due=is_due,
            recommended_action="Follow up regarding agreement (opened, not yet signed)." if is_due
            else "Agreement recently opened -- give the client a little more time.",
            template_category=TemplateCategory.AGREEMENT_OPEN,
            tone=Tone.ACTION_ORIENTED,
            priority=priority,
            reason="Agreement Opened - Signature Pending: "
                   f"{days_since_agreement_opened} working day(s) since it was opened.",
            days_since_last_contact=days_since_contact,
            days_since_agreement_sent=days_since_agreement_sent,
            days_since_agreement_opened=days_since_agreement_opened,
        )

    if client.agreement_status == "PENDING_SIGNATURE":
        is_due = days_since_contact is not None and days_since_contact >= 3
        return FollowUpDecision(
            is_due=is_due,
            recommended_action="Send a direct nudge/reminder for signature." if is_due
            else "Signature pending -- not yet due for another nudge.",
            template_category=TemplateCategory.AGREEMENT_FINAL,
            tone=Tone.SUBTLE_URGENCY,
            priority=Priority.HIGH if is_due else Priority.MEDIUM,
            reason="Agreement pending signature; "
                   f"{days_since_contact} working day(s) since last contact.",
            days_since_last_contact=days_since_contact,
            days_since_agreement_sent=days_since_agreement_sent,
            days_since_agreement_opened=days_since_agreement_opened,
        )

    # SENT but not opened yet.
    is_due = days_since_agreement_sent is not None and days_since_agreement_sent >= 3
    return FollowUpDecision(
        is_due=is_due,
        recommended_action="Send an initial agreement check-in." if is_due
        else "Agreement recently sent -- no reminder due yet.",
        template_category=TemplateCategory.AGREEMENT_REMINDER,
        tone=Tone.FRIENDLY_ENGAGING,
        priority=Priority.MEDIUM if is_due else Priority.LOW,
        reason=f"Agreement sent {days_since_agreement_sent} working day(s) ago, not yet opened.",
        days_since_last_contact=days_since_contact,
        days_since_agreement_sent=days_since_agreement_sent,
        days_since_agreement_opened=days_since_agreement_opened,
    )


def _meeting_decision(client: ClientSnapshot, days_since_contact: Optional[int]) -> FollowUpDecision:
    if client.stage == ClientStage.MEETING_REQUESTED:
        is_due = days_since_contact is not None and days_since_contact >= 2
        return FollowUpDecision(
            is_due=is_due,
            recommended_action="Follow up to schedule the meeting." if is_due else "Awaiting meeting scheduling response.",
            template_category=TemplateCategory.MEETING_CONFIRMATION,
            tone=Tone.ACTION_ORIENTED,
            priority=Priority.MEDIUM,
            reason="Meeting requested but not yet scheduled.",
            days_since_last_contact=days_since_contact,
        )
    if client.stage == ClientStage.MEETING_SCHEDULED:
        return FollowUpDecision(
            is_due=True,
            recommended_action="Send meeting confirmation request.",
            template_category=TemplateCategory.MEETING_CONFIRMATION,
            tone=Tone.ACTION_ORIENTED,
            priority=Priority.HIGH,
            reason="Meeting scheduled -- confirmation should be requested.",
            days_since_last_contact=days_since_contact,
        )
    # MEETING_CONFIRMED
    is_due_reminder = (
        client.meeting_date is not None and (client.meeting_date - date.today()).days in (0, 1)
    )
    return FollowUpDecision(
        is_due=is_due_reminder,
        recommended_action="Send meeting reminder." if is_due_reminder else "Meeting confirmed -- no action yet.",
        template_category=TemplateCategory.MEETING_REMINDER,
        tone=Tone.POLITE_PROFESSIONAL,
        priority=Priority.HIGH if is_due_reminder else Priority.LOW,
        reason="Meeting confirmed; reminder sent close to the meeting date only.",
        days_since_last_contact=days_since_contact,
    )
