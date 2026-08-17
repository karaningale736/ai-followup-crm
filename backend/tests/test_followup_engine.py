from datetime import datetime, timedelta
from app.core.enums import ClientStage
from app.services.followup_engine import analyze, ClientSnapshot


def _dt_days_ago(n):
    return datetime.utcnow() - timedelta(days=n)


def test_new_lead_not_due_before_two_working_days():
    snap = ClientSnapshot(stage=ClientStage.NEW_LEAD, last_contact_date=_dt_days_ago(1))
    decision = analyze(snap)
    assert decision.is_due is False


def test_followup_1_due_after_window():
    snap = ClientSnapshot(stage=ClientStage.INITIAL_FOLLOW_UP, last_contact_date=_dt_days_ago(5),
                           followup_count=1)
    decision = analyze(snap)
    assert decision.is_due is True
    assert decision.template_category.value == "FOLLOW_UP_2"


def test_followup_3_recommends_new_subject_language():
    snap = ClientSnapshot(stage=ClientStage.FOLLOW_UP_3, last_contact_date=_dt_days_ago(8),
                           followup_count=3)
    decision = analyze(snap)
    assert "NEW subject" in decision.recommended_action or decision.template_category.value == "FOLLOW_UP_3"


def test_terminal_stage_never_due():
    snap = ClientSnapshot(stage=ClientStage.DECLINED, last_contact_date=_dt_days_ago(30))
    decision = analyze(snap)
    assert decision.is_due is False
    assert decision.template_category is None


def test_signed_is_terminal():
    snap = ClientSnapshot(stage=ClientStage.SIGNED, last_contact_date=_dt_days_ago(30))
    decision = analyze(snap)
    assert decision.is_due is False


def test_agreement_opened_signature_pending_high_priority():
    snap = ClientSnapshot(
        stage=ClientStage.AGREEMENT_OPENED,
        agreement_status="OPENED",
        agreement_sent_at=_dt_days_ago(10),
        agreement_opened_at=_dt_days_ago(4),
    )
    decision = analyze(snap)
    assert decision.is_due is True
    assert decision.priority.value == "HIGH"
    assert decision.template_category.value == "AGREEMENT_OPEN"


def test_agreement_sent_not_opened_lower_priority():
    snap = ClientSnapshot(
        stage=ClientStage.AGREEMENT_SENT,
        agreement_status="SENT",
        agreement_sent_at=_dt_days_ago(4),
    )
    decision = analyze(snap)
    assert decision.template_category.value == "AGREEMENT_REMINDER"


def test_budget_objection_without_offer_waits():
    snap = ClientSnapshot(stage=ClientStage.BUDGET_OBJECTION, has_approved_offer=False)
    decision = analyze(snap)
    assert decision.is_due is False
    assert "approved" in decision.reason.lower()


def test_budget_objection_with_approved_offer_is_due():
    snap = ClientSnapshot(stage=ClientStage.BUDGET_OBJECTION, has_approved_offer=True)
    decision = analyze(snap)
    assert decision.is_due is True
    assert decision.template_category.value == "SPECIAL_OFFER"


def test_declined_client_never_gets_normal_followup_template():
    snap = ClientSnapshot(stage=ClientStage.DECLINED)
    decision = analyze(snap)
    assert decision.template_category is None


def test_participation_pending_due_after_two_days():
    snap = ClientSnapshot(stage=ClientStage.PARTICIPATION_PENDING, last_contact_date=_dt_days_ago(4))
    decision = analyze(snap)
    assert decision.is_due is True
    assert decision.template_category.value == "PARTICIPATION_CONFIRMATION"


def test_no_last_contact_date_is_not_due():
    snap = ClientSnapshot(stage=ClientStage.NEW_LEAD, last_contact_date=None)
    decision = analyze(snap)
    assert decision.is_due is False
