from datetime import datetime
from sqlalchemy import Integer, DateTime, String, Text, Boolean, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.core.enums import ClientStage, Tone, TemplateCategory


class Template(Base):
    __tablename__ = "templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    category: Mapped[TemplateCategory] = mapped_column(SAEnum(TemplateCategory), index=True)
    stage: Mapped[ClientStage | None] = mapped_column(SAEnum(ClientStage), nullable=True)
    subject: Mapped[str] = mapped_column(String(300))
    body: Mapped[str] = mapped_column(Text)
    tone: Mapped[Tone] = mapped_column(SAEnum(Tone), default=Tone.POLITE_PROFESSIONAL)
    priority: Mapped[str] = mapped_column(String(20), default="MEDIUM")
    conditions: Mapped[str] = mapped_column(Text, default="")  # JSON-encoded condition notes
    variables: Mapped[str] = mapped_column(Text, default="")   # JSON-encoded list of placeholder names
    source: Mapped[str] = mapped_column(String(200), default="Business Follow-Up Workflow")
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
