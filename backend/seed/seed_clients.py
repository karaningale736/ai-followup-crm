"""
Seeds 17 fictional clients spanning the full stage lifecycle, plus matching
Agreement/Meeting rows where relevant. Run with: python -m seed.seed_clients
Run seed_templates first (or `python -m seed.seed_all`).
"""

from datetime import datetime, timedelta, date, time

from app.core.database import SessionLocal, init_db
from app.core.enums import ClientStage, Priority, AgreementStatus, MeetingStatus
from app.models.client import Client
from app.models.agreement import Agreement
from app.models.meeting import Meeting

now = datetime.utcnow()


def days_ago(n):
    return now - timedelta(days=n)


CLIENTS = [
    dict(first_name="Amara", last_name="Okafor", company_name="Northwind Traders",
         email="amara.okafor@northwindtraders.example", current_stage=ClientStage.NEW_LEAD,
         priority=Priority.MEDIUM, assigned_manager="J. Reyes", feature_title="Cover Feature",
         edition_title="Q4 Innovators Edition"),
    dict(first_name="Lucas", last_name="Ferreira", company_name="Solaris Analytics",
         email="lucas.ferreira@solarisanalytics.example", current_stage=ClientStage.INITIAL_FOLLOW_UP,
         priority=Priority.MEDIUM, assigned_manager="J. Reyes", followup_count=1,
         last_contact_date=days_ago(3), feature_title="Executive Spotlight",
         edition_title="Q4 Innovators Edition"),
    dict(first_name="Priya", last_name="Menon", company_name="Verdant Foods",
         email="priya.menon@verdantfoods.example", current_stage=ClientStage.FOLLOW_UP_2,
         priority=Priority.MEDIUM, assigned_manager="T. Kim", followup_count=2,
         last_contact_date=days_ago(4), feature_title="Industry Roundtable",
         edition_title="Sustainability Edition"),
    dict(first_name="Marcus", last_name="Webb", company_name="Ironclad Logistics",
         email="marcus.webb@ironcladlogistics.example", current_stage=ClientStage.FOLLOW_UP_3,
         priority=Priority.HIGH, assigned_manager="T. Kim", followup_count=3,
         last_contact_date=days_ago(7), feature_title="Case Study Feature",
         edition_title="Supply Chain Edition"),
    dict(first_name="Elena", last_name="Ionescu", company_name="Bright Path Financial",
         email="elena.ionescu@brightpathfinancial.example", current_stage=ClientStage.INTERESTED,
         priority=Priority.MEDIUM, assigned_manager="J. Reyes", last_contact_date=days_ago(1),
         feature_title="Executive Interview", edition_title="Q4 Innovators Edition"),
    dict(first_name="Daniel", last_name="Osei", company_name="Kade Robotics",
         email="daniel.osei@kaderobotics.example", current_stage=ClientStage.MEETING_REQUESTED,
         priority=Priority.MEDIUM, assigned_manager="T. Kim", last_contact_date=days_ago(2),
         feature_title="Tech Spotlight", edition_title="Innovation in Manufacturing"),
    dict(first_name="Sofia", last_name="Bianchi", company_name="Lumen Health Group",
         email="sofia.bianchi@lumenhealthgroup.example", current_stage=ClientStage.MEETING_SCHEDULED,
         priority=Priority.HIGH, assigned_manager="J. Reyes", last_contact_date=days_ago(1),
         feature_title="Cover Feature", edition_title="Healthcare Leaders Edition"),
    dict(first_name="Ravi", last_name="Chandra", company_name="Aster Cloud Systems",
         email="ravi.chandra@astercloudsystems.example", current_stage=ClientStage.MEETING_COMPLETED,
         priority=Priority.MEDIUM, assigned_manager="T. Kim", last_contact_date=days_ago(1),
         feature_title="Product Spotlight", edition_title="Cloud & Infrastructure Edition"),
    dict(first_name="Grace", last_name="Muthoni", company_name="Baobab Ventures",
         email="grace.muthoni@baobabventures.example", current_stage=ClientStage.AGREEMENT_SENT,
         priority=Priority.MEDIUM, assigned_manager="J. Reyes", last_contact_date=days_ago(2),
         offer_amount=1200, feature_title="Investor Spotlight", edition_title="Growth Markets Edition"),
    dict(first_name="Hiroshi", last_name="Tanaka", company_name="Kensho Dynamics",
         email="hiroshi.tanaka@kenshodynamics.example", current_stage=ClientStage.AGREEMENT_OPENED,
         priority=Priority.HIGH, assigned_manager="T. Kim", last_contact_date=days_ago(3),
         offer_amount=1500, feature_title="Cover Feature", edition_title="Innovation in Manufacturing"),
    dict(first_name="Isabela", last_name="Cardoso", company_name="Nimbus Retail Co.",
         email="isabela.cardoso@nimbusretail.example", current_stage=ClientStage.AGREEMENT_PENDING_SIGNATURE,
         priority=Priority.HIGH, assigned_manager="J. Reyes", last_contact_date=days_ago(4),
         offer_amount=950, feature_title="Executive Interview", edition_title="Retail Futures Edition"),
    dict(first_name="Tobias", last_name="Lindgren", company_name="Frostline Energy",
         email="tobias.lindgren@frostlineenergy.example", current_stage=ClientStage.BUDGET_OBJECTION,
         priority=Priority.MEDIUM, assigned_manager="T. Kim", last_contact_date=days_ago(2),
         client_concern="Client says the feature package is above their current marketing budget.",
         feature_title="Sponsored Feature", edition_title="Energy Transition Edition"),
    dict(first_name="Nadia", last_name="Haddad", company_name="Cedarline Consulting",
         email="nadia.haddad@cedarlineconsulting.example", current_stage=ClientStage.SPECIAL_OFFER,
         priority=Priority.HIGH, assigned_manager="J. Reyes", last_contact_date=days_ago(1),
         offer_amount=800, feature_title="Sponsored Feature", edition_title="Energy Transition Edition",
         notes="Approved reduced offer of USD 800 (original USD 1200)."),
    dict(first_name="Owen", last_name="Fitzgerald", company_name="Harborview Capital",
         email="owen.fitzgerald@harborviewcapital.example", current_stage=ClientStage.DECLINED,
         priority=Priority.LOW, assigned_manager="T. Kim", last_contact_date=days_ago(5),
         feature_title="Investor Spotlight", edition_title="Growth Markets Edition"),
    dict(first_name="Chiara", last_name="Romano", company_name="Vela Biotech",
         email="chiara.romano@velabiotech.example", current_stage=ClientStage.SIGNED,
         priority=Priority.LOW, assigned_manager="J. Reyes", last_contact_date=days_ago(6),
         offer_amount=1800, feature_title="Cover Feature", edition_title="Life Sciences Edition"),
    dict(first_name="Julian", last_name="Voss", company_name="Meridian Steelworks",
         email="julian.voss@meridiansteelworks.example", current_stage=ClientStage.COMPLETED,
         priority=Priority.LOW, assigned_manager="T. Kim", last_contact_date=days_ago(20),
         offer_amount=1400, feature_title="Case Study Feature", edition_title="Industrial Edition"),
    dict(first_name="Fatima", last_name="Al-Sayed", company_name="Palmwave Media",
         email="fatima.alsayed@palmwavemedia.example", current_stage=ClientStage.PARTICIPATION_PENDING,
         priority=Priority.MEDIUM, assigned_manager="J. Reyes", last_contact_date=days_ago(2),
         feature_title="Panel Discussion", edition_title="Media & Culture Edition"),
]


def seed():
    init_db()
    db = SessionLocal()
    try:
        if db.query(Client).count() > 0:
            print("Clients already seeded -- skipping.")
            return

        for data in CLIENTS:
            client = Client(**data)
            db.add(client)
            db.flush()  # get client.id

            if client.current_stage == ClientStage.AGREEMENT_SENT:
                db.add(Agreement(client_id=client.id, status=AgreementStatus.SENT,
                                  sent_at=client.last_contact_date))
            elif client.current_stage == ClientStage.AGREEMENT_OPENED:
                db.add(Agreement(client_id=client.id, status=AgreementStatus.OPENED,
                                  sent_at=days_ago(6), opened_at=client.last_contact_date))
            elif client.current_stage == ClientStage.AGREEMENT_PENDING_SIGNATURE:
                db.add(Agreement(client_id=client.id, status=AgreementStatus.PENDING_SIGNATURE,
                                  sent_at=days_ago(8), opened_at=days_ago(6)))
            elif client.current_stage == ClientStage.SIGNED:
                db.add(Agreement(client_id=client.id, status=AgreementStatus.SIGNED,
                                  sent_at=days_ago(12), opened_at=days_ago(10), signed_at=days_ago(6)))
            elif client.current_stage == ClientStage.DECLINED:
                db.add(Agreement(client_id=client.id, status=AgreementStatus.DECLINED,
                                  sent_at=days_ago(9), declined_at=days_ago(5)))

            if client.current_stage == ClientStage.MEETING_REQUESTED:
                db.add(Meeting(client_id=client.id, status=MeetingStatus.REQUESTED))
            elif client.current_stage == ClientStage.MEETING_SCHEDULED:
                db.add(Meeting(client_id=client.id, status=MeetingStatus.SCHEDULED,
                                meeting_date=date.today() + timedelta(days=2),
                                meeting_time=time(15, 0), assigned_colleague="T. Kim"))
            elif client.current_stage == ClientStage.MEETING_COMPLETED:
                db.add(Meeting(client_id=client.id, status=MeetingStatus.COMPLETED,
                                meeting_date=date.today() - timedelta(days=1),
                                meeting_time=time(11, 0), assigned_colleague="T. Kim"))

        db.commit()
        print(f"Seeded {len(CLIENTS)} clients.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
