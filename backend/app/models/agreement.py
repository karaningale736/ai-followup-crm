from datetime import datetime
from sqlalchemy import Integer, DateTime, String, Text, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import AgreementStatus


class Agreement(Base):
    __tablename__ = "agreements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), index=True)

    agreement_url: Mapped[str] = mapped_column(String(500), default="")
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    opened_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    signed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    declined_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[AgreementStatus] = mapped_column(
        SAEnum(AgreementStatus), default=AgreementStatus.NOT_SENT
    )
    notes: Mapped[str] = mapped_column(Text, default="")

    client = relationship("Client", back_populates="agreements")
