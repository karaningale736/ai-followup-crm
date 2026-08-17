from typing import Optional, Dict, Any
from pydantic import BaseModel

from app.core.enums import Tone, Priority, TemplateCategory


class AnalyzeRequest(BaseModel):
    client_id: int


class AnalyzeResponse(BaseModel):
    client_id: int
    current_stage: str
    is_due: bool
    recommended_action: str
    template_category: Optional[str]
    tone: str
    priority: str
    reason: str
    days_since_last_contact: Optional[int] = None
    days_since_agreement_sent: Optional[int] = None
    days_since_agreement_opened: Optional[int] = None


class GenerateEmailRequest(BaseModel):
    client_id: int
    template_id: Optional[int] = None
    additional_variables: Dict[str, Any] = {}


class GenerateEmailResponse(BaseModel):
    client_id: int
    template_id: Optional[int]
    subject: str
    email_body: str
    cta: str
    tone: str
    template_category: Optional[str]
