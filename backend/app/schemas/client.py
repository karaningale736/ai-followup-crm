from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr

from app.core.enums import ClientStage, Priority


class ClientBase(BaseModel):
    first_name: str
    last_name: str = ""
    company_name: str = ""
    job_title: str = ""
    email: str
    phone: str = ""
    country: str = ""
    timezone: str = ""
    edition_title: str = ""
    feature_title: str = ""
    assigned_manager: str = ""
    lead_source: str = ""
    client_status: str = "ACTIVE"
    current_stage: ClientStage = ClientStage.NEW_LEAD
    offer_amount: Optional[float] = None
    currency: str = "USD"
    client_concern: str = ""
    notes: str = ""
    priority: Priority = Priority.MEDIUM


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    timezone: Optional[str] = None
    edition_title: Optional[str] = None
    feature_title: Optional[str] = None
    assigned_manager: Optional[str] = None
    lead_source: Optional[str] = None
    client_status: Optional[str] = None
    current_stage: Optional[ClientStage] = None
    offer_amount: Optional[float] = None
    currency: Optional[str] = None
    client_concern: Optional[str] = None
    notes: Optional[str] = None
    priority: Optional[Priority] = None
    last_contact_date: Optional[datetime] = None


class ClientOut(ClientBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    last_contact_date: Optional[datetime] = None
    last_email_sent_date: Optional[datetime] = None
    last_email_received_date: Optional[datetime] = None
    next_followup_date: Optional[datetime] = None
    followup_count: int
    created_at: datetime
    updated_at: datetime
