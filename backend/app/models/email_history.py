from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import EmailDirection, EmailStatus, ClientStage


class EmailHistory(Base):
    __tablename__ = "email_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), index=True)

    direction: Mapped[EmailDirection] = mapped_column(SAEnum(EmailDirection))
    subject: Mapped[str] = mapped_column(String(300), default="")
    body: Mapped[str] = mapped_column(Text, default="")

    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    received_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    template_id: Mapped[int | None] = mapped_column(ForeignKey("templates.id"), nullable=True)
    stage: Mapped[ClientStage | None] = mapped_column(SAEnum(ClientStage), nullable=True)
    status: Mapped[EmailStatus] = mapped_column(SAEnum(EmailStatus), default=EmailStatus.DRAFT)

    sender: Mapped[str] = mapped_column(String(200), default="")
    recipient: Mapped[str] = mapped_column(String(200), default="")
    message_id: Mapped[str] = mapped_column(String(200), default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    client = relationship("Client", back_populates="emails")
