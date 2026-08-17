from datetime import date, time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.enums import MeetingStatus
from app.models.meeting import Meeting
from app.models.client import Client

router = APIRouter(prefix="/api/meetings", tags=["meetings"])


class MeetingIn(BaseModel):
    client_id: int
    meeting_date: Optional[date] = None
    meeting_time: Optional[time] = None
    timezone: str = ""
    meeting_link: str = ""
    assigned_colleague: str = ""
    status: MeetingStatus = MeetingStatus.REQUESTED
    notes: str = ""


class MeetingUpdate(BaseModel):
    meeting_date: Optional[date] = None
    meeting_time: Optional[time] = None
    timezone: Optional[str] = None
    meeting_link: Optional[str] = None
    assigned_colleague: Optional[str] = None
    status: Optional[MeetingStatus] = None
    notes: Optional[str] = None


class MeetingOut(MeetingIn):
    id: int

    class Config:
        from_attributes = True


@router.post("", response_model=MeetingOut)
def create_meeting(payload: MeetingIn, db: Session = Depends(get_db)):
    client = db.get(Client, payload.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    meeting = Meeting(**payload.model_dump())
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting


@router.get("", response_model=List[MeetingOut])
def list_meetings(db: Session = Depends(get_db), client_id: Optional[int] = None):
    q = db.query(Meeting)
    if client_id:
        q = q.filter(Meeting.client_id == client_id)
    return q.order_by(Meeting.meeting_date).all()


@router.put("/{meeting_id}", response_model=MeetingOut)
def update_meeting(meeting_id: int, payload: MeetingUpdate, db: Session = Depends(get_db)):
    meeting = db.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(meeting, field, value)
    db.commit()
    db.refresh(meeting)
    return meeting
