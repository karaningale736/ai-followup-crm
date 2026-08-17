from datetime import datetime
from sqlalchemy import Integer, DateTime, Text, String, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import ClientStage


class FollowUp(Base):
    __tablename__ = "follow_ups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), index=True)

    followup_number: Mapped[int] = mapped_column(Integer, default=1)
    stage: Mapped[ClientStage] = mapped_column(SAEnum(ClientStage))
    scheduled_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="PENDING")  # PENDING/DUE/COMPLETED/SKIPPED
    template_id: Mapped[int | None] = mapped_column(ForeignKey("templates.id"), nullable=True)
    recommended_action: Mapped[str] = mapped_column(Text, default="")
    reason: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    client = relationship("Client", back_populates="followups")
