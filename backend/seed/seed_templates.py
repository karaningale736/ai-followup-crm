"""
Seeds the Template table with one approved template per category from the
supplied business workflow. Run with: python -m seed.seed_templates
"""

from app.core.database import SessionLocal, init_db
from app.core.enums import TemplateCategory, ClientStage, Tone
from app.models.template import Template

TEMPLATES = [
    dict(
        name="Initial Follow-Up 1",
        category=TemplateCategory.FOLLOW_UP_1,
        stage=ClientStage.INITIAL_FOLLOW_UP,
        subject="Following up: {feature_title} for {edition_title}",
        body=(
            "Hi {client_first_name},\n\n"
            "I wanted to check in and see if you had a chance to review the details "
            "we shared about {feature_title} for {edition_title}. I'd love to hear your "
            "thoughts and answer any questions you may have.\n\n"
            "Let me know how you'd like to proceed.\n\n"
            "Best regards,\n{assigned_manager}"
        ),
        tone=Tone.POLITE_PROFESSIONAL,
        priority="MEDIUM",
        variables="client_first_name,feature_title,edition_title,assigned_manager",
    ),
    dict(
        name="Follow-Up 2",
        category=TemplateCategory.FOLLOW_UP_2,
        stage=ClientStage.FOLLOW_UP_2,
        subject="Following up: {feature_title} for {edition_title}",
        body=(
            "Hi {client_first_name},\n\n"
            "Just circling back on my previous note about {feature_title}. "
            "I understand things get busy -- happy to clarify anything or adjust timing "
            "if useful. Would you like to proceed, or do you have questions I can address?\n\n"
            "Best regards,\n{assigned_manager}"
        ),
        tone=Tone.FRIENDLY_ENGAGING,
        priority="MEDIUM",
        variables="client_first_name,feature_title,edition_title,assigned_manager",
    ),
    dict(
        name="Follow-Up 3 (New Subject)",
        category=TemplateCategory.FOLLOW_UP_3,
        stage=ClientStage.FOLLOW_UP_3,
        subject="Quick question about {company_name} and {edition_title}",
        body=(
            "Hi {client_first_name},\n\n"
            "I don't want to keep filling your inbox, so this will be my last note for now. "
            "If {feature_title} is still of interest, I'm happy to pick things back up whenever "
            "works for you -- just let me know.\n\n"
            "Best regards,\n{assigned_manager}"
        ),
        tone=Tone.FRIENDLY_ENGAGING,
        priority="LOW",
        variables="client_first_name,company_name,feature_title,edition_title,assigned_manager",
    ),
    dict(
        name="Participation Confirmation Request",
        category=TemplateCategory.PARTICIPATION_CONFIRMATION,
        stage=ClientStage.PARTICIPATION_PENDING,
        subject="Confirming your participation in {edition_title}",
        body=(
            "Hi {client_first_name},\n\n"
            "Could you confirm whether {company_name} would like to move forward with "
            "{feature_title}? Once confirmed, I'll take care of the next steps on our end.\n\n"
            "Best regards,\n{assigned_manager}"
        ),
        tone=Tone.ACTION_ORIENTED,
        priority="MEDIUM",
        variables="client_first_name,company_name,feature_title,edition_title,assigned_manager",
    ),
    dict(
        name="Meeting Confirmation",
        category=TemplateCategory.MEETING_CONFIRMATION,
        stage=ClientStage.MEETING_SCHEDULED,
        subject="Confirming our upcoming call",
        body=(
            "Hi {client_first_name},\n\n"
            "Just confirming our call at {meeting_time} on {meeting_date}. It should take "
            "about 10-15 minutes to cover {feature_title} and next steps. If that time no "
            "longer works, let me know a better time and I'll adjust.\n\n"
            "Best regards,\n{assigned_manager}"
        ),
        tone=Tone.ACTION_ORIENTED,
        priority="HIGH",
        variables="client_first_name,meeting_time,meeting_date,feature_title,assigned_manager",
    ),
    dict(
        name="Meeting Reminder",
        category=TemplateCategory.MEETING_REMINDER,
        stage=ClientStage.MEETING_CONFIRMED,
        subject="Reminder: our call at {meeting_time}",
        body=(
            "Hi {client_first_name},\n\n"
            "Quick reminder about our call at {meeting_time} on {meeting_date}. "
            "Here's the link: {meeting_link}. Talk soon!\n\n"
            "Best regards,\n{assigned_manager}"
        ),
        tone=Tone.POLITE_PROFESSIONAL,
        priority="HIGH",
        variables="client_first_name,meeting_time,meeting_date,meeting_link,assigned_manager",
    ),
    dict(
        name="Meeting Reschedule",
        category=TemplateCategory.MEETING_RESCHEDULE,
        stage=ClientStage.MEETING_SCHEDULED,
        subject="Re: our call -- happy to find a new time",
        body=(
            "Hi {client_first_name},\n\n"
            "No problem at all -- could you share an alternative time (or a good number to "
            "reach you) and I'll get it set up?\n\n"
            "Best regards,\n{assigned_manager}"
        ),
        tone=Tone.FRIENDLY_ENGAGING,
        priority="MEDIUM",
        variables="client_first_name,assigned_manager",
    ),
    dict(
        name="Call Attempt Follow-Up",
        category=TemplateCategory.CALL_ATTEMPT,
        stage=ClientStage.MEETING_REQUESTED,
        subject="Tried reaching you -- {feature_title}",
        body=(
            "Hi {client_first_name},\n\n"
            "I tried giving you a call regarding {feature_title} but wasn't able to connect. "
            "Let me know a good time and I'll follow up, or feel free to reach me directly.\n\n"
            "Best regards,\n{assigned_manager}"
        ),
        tone=Tone.POLITE_PROFESSIONAL,
        priority="MEDIUM",
        variables="client_first_name,feature_title,assigned_manager",
    ),
    dict(
        name="Manager/ID Participation Quick Update",
        category=TemplateCategory.MANAGER_ID,
        stage=ClientStage.PARTICIPATION_PENDING,
        subject="Quick update needed -- {company_name}",
        body=(
            "Hi {client_first_name},\n\n"
            "Could you send over the manager ID/contact details for {company_name} so we can "
            "finalize participation on our end?\n\n"
            "Best regards,\n{assigned_manager}"
        ),
        tone=Tone.ACTION_ORIENTED,
        priority="MEDIUM",
        variables="client_first_name,company_name,assigned_manager",
    ),
    dict(
        name="Agreement Sent",
        category=TemplateCategory.AGREEMENT_SENT,
        stage=ClientStage.AGREEMENT_SENT,
        subject="Media Partnership Agreement -- {company_name}",
        body=(
            "Hi {client_first_name},\n\n"
            "Please find attached the Media Partnership Agreement for {feature_title}. "
            "Let me know if anything needs adjusting, and feel free to reach out with questions.\n\n"
            "Best regards,\n{assigned_manager}"
        ),
        tone=Tone.POLITE_PROFESSIONAL,
        priority="MEDIUM",
        variables="client_first_name,company_name,feature_title,assigned_manager",
    ),
    dict(
        name="Agreement Reminder",
        category=TemplateCategory.AGREEMENT_REMINDER,
        stage=ClientStage.AGREEMENT_SENT,
        subject="Re: Media Partnership Agreement -- {company_name}",
        body=(
            "Hi {client_first_name},\n\n"
            "Just checking in on the agreement I sent over -- happy to answer any questions "
            "or hop on a quick call if useful.\n\n"
            "Best regards,\n{assigned_manager}"
        ),
        tone=Tone.FRIENDLY_ENGAGING,
        priority="MEDIUM",
        variables="client_first_name,company_name,assigned_manager",
    ),
    dict(
        name="Agreement Opened -- Signature Pending",
        category=TemplateCategory.AGREEMENT_OPEN,
        stage=ClientStage.AGREEMENT_OPENED,
        subject="Re: Media Partnership Agreement -- {company_name}",
        body=(
            "Hi {client_first_name},\n\n"
            "I saw you had a chance to open the agreement -- let me know if you ran into any "
            "technical issues, or if a short call would help walk through anything before signing.\n\n"
            "Best regards,\n{assigned_manager}"
        ),
        tone=Tone.ACTION_ORIENTED,
        priority="HIGH",
        variables="client_first_name,company_name,assigned_manager",
    ),
    dict(
        name="Agreement Call Offer",
        category=TemplateCategory.AGREEMENT_CALL,
        stage=ClientStage.AGREEMENT_CALL_REQUIRED,
        subject="Quick call to review the agreement?",
        body=(
            "Hi {client_first_name},\n\n"
            "Would a short 10-15 minute call help clarify anything in the agreement? "
            "Happy to set one up whenever works for you.\n\n"
            "Best regards,\n{assigned_manager}"
        ),
        tone=Tone.ACTION_ORIENTED,
        priority="HIGH",
        variables="client_first_name,assigned_manager",
    ),
    dict(
        name="Agreement Final Follow-Up",
        category=TemplateCategory.AGREEMENT_FINAL,
        stage=ClientStage.AGREEMENT_FINAL_FOLLOW_UP,
        subject="Following up one more time -- {company_name}",
        body=(
            "Hi {client_first_name},\n\n"
            "I don't want to be a bother, so this will be my last check-in on the agreement. "
            "If you'd still like to move forward, just let me know and I'll pick things back up "
            "right away.\n\n"
            "Best regards,\n{assigned_manager}"
        ),
        tone=Tone.SUBTLE_URGENCY,
        priority="HIGH",
        variables="client_first_name,company_name,assigned_manager",
    ),
    dict(
        name="Declined -- Thank You",
        category=TemplateCategory.DECLINED,
        stage=ClientStage.DECLINED,
        subject="Thank you for your time",
        body=(
            "Hi {client_first_name},\n\n"
            "Thank you for letting us know, and for taking the time to consider {feature_title}. "
            "I completely understand, and I'd be glad to reconnect down the line if circumstances "
            "change.\n\n"
            "Wishing you and {company_name} all the best.\n\n"
            "Best regards,\n{assigned_manager}"
        ),
        tone=Tone.POLITE_PROFESSIONAL,
        priority="LOW",
        variables="client_first_name,feature_title,company_name,assigned_manager",
    ),
    dict(
        name="Budget Objection Acknowledgment",
        category=TemplateCategory.BUDGET_OBJECTION,
        stage=ClientStage.BUDGET_OBJECTION,
        subject="Re: {feature_title} -- budget",
        body=(
            "Hi {client_first_name},\n\n"
            "Thanks for being upfront about budget -- that's really helpful. Let me check "
            "with my team on options and get back to you shortly.\n\n"
            "Best regards,\n{assigned_manager}"
        ),
        tone=Tone.POLITE_PROFESSIONAL,
        priority="MEDIUM",
        variables="client_first_name,feature_title,assigned_manager",
    ),
    dict(
        name="Special Offer (Approved)",
        category=TemplateCategory.SPECIAL_OFFER,
        stage=ClientStage.SPECIAL_OFFER,
        subject="An updated offer for {company_name}",
        body=(
            "Hi {client_first_name},\n\n"
            "Following up on our conversation about budget -- I've been able to put together "
            "an adjusted offer of {currency} {offer_amount} for {feature_title}. "
            "Let me know if that works and I'll get things moving.\n\n"
            "Best regards,\n{assigned_manager}"
        ),
        tone=Tone.FRIENDLY_ENGAGING,
        priority="HIGH",
        variables="client_first_name,company_name,currency,offer_amount,feature_title,assigned_manager",
    ),
    dict(
        name="Payment Discussion",
        category=TemplateCategory.PAYMENT_DISCUSSION,
        stage=ClientStage.PAYMENT_DISCUSSION,
        subject="Finalizing payment details -- {company_name}",
        body=(
            "Hi {client_first_name},\n\n"
            "Great to hear you'd like to move forward. Let me know the best way to coordinate "
            "on payment details and I'll take care of the rest on our end.\n\n"
            "Best regards,\n{assigned_manager}"
        ),
        tone=Tone.ACTION_ORIENTED,
        priority="HIGH",
        variables="client_first_name,company_name,assigned_manager",
    ),
    dict(
        name="Virtual Participation Option",
        category=TemplateCategory.VIRTUAL_PARTICIPATION,
        stage=ClientStage.VIRTUAL_PARTICIPATION,
        subject="Virtual participation option for {edition_title}",
        body=(
            "Hi {client_first_name},\n\n"
            "If attending in person isn't feasible, we're also able to offer a virtual "
            "participation option for {feature_title}. Would that work better for you?\n\n"
            "Best regards,\n{assigned_manager}"
        ),
        tone=Tone.FRIENDLY_ENGAGING,
        priority="MEDIUM",
        variables="client_first_name,edition_title,feature_title,assigned_manager",
    ),
    dict(
        name="Title Suggestion Request",
        category=TemplateCategory.TITLE_SUGGESTION,
        stage=None,
        subject="A quick request -- title for {feature_title}",
        body=(
            "Hi {client_first_name},\n\n"
            "Could you share the exact title/designation you'd like used for {feature_title}? "
            "This helps us make sure everything is accurate.\n\n"
            "Best regards,\n{assigned_manager}"
        ),
        tone=Tone.POLITE_PROFESSIONAL,
        priority="LOW",
        variables="client_first_name,feature_title,assigned_manager",
    ),
    dict(
        name="Image Request",
        category=TemplateCategory.IMAGE_REQUEST,
        stage=None,
        subject="Image needed for {feature_title}",
        body=(
            "Hi {client_first_name},\n\n"
            "When you get a chance, could you send over a high-resolution image/logo for use "
            "with {feature_title}?\n\n"
            "Best regards,\n{assigned_manager}"
        ),
        tone=Tone.POLITE_PROFESSIONAL,
        priority="LOW",
        variables="client_first_name,feature_title,assigned_manager",
    ),
]


def seed():
    init_db()
    db = SessionLocal()
    try:
        existing = {t.category for t in db.query(Template).all()}
        added = 0
        for data in TEMPLATES:
            if data["category"] in existing:
                continue
            db.add(Template(**data))
            added += 1
        db.commit()
        print(f"Seeded {added} templates ({len(existing)} already present).")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
