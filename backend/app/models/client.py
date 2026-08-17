from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, Text, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import ClientStage, Priority


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100), default="")
    company_name: Mapped[str] = mapped_column(String(200), default="")
    job_title: Mapped[str] = mapped_column(String(150), default="")
    email: Mapped[str] = mapped_column(String(200), index=True)
    phone: Mapped[str] = mapped_column(String(50), default="")
    country: Mapped[str] = mapped_column(String(100), default="")
    timezone: Mapped[str] = mapped_column(String(50), default="")
    edition_title: Mapped[str] = mapped_column(String(200), default="")
    feature_title: Mapped[str] = mapped_column(String(200), default="")
    assigned_manager: Mapped[str] = mapped_column(String(150), default="")
    lead_source: Mapped[str] = mapped_column(String(150), default="")

    client_status: Mapped[str] = mapped_column(String(50), default="ACTIVE")
    current_stage: Mapped[ClientStage] = mapped_column(
        SAEnum(ClientStage), default=ClientStage.NEW_LEAD, index=True
    )

    offer_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    client_concern: Mapped[str] = mapped_column(Text, default="")

    last_contact_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_email_sent_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_email_received_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_followup_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    followup_count: Mapped[int] = mapped_column(Integer, default=0)
    priority: Mapped[Priority] = mapped_column(SAEnum(Priority), default=Priority.MEDIUM)
    notes: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    emails = relationship("EmailHistory", back_populates="client", cascade="all, delete-orphan")
    followups = relationship("FollowUp", back_populates="client", cascade="all, delete-orphan")
    meetings = relationship("Meeting", back_populates="client", cascade="all, delete-orphan")
    agreements = relationship("Agreement", back_populates="client", cascade="all, delete-orphan")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()
