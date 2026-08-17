from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.enums import TemplateCategory, ClientStage, Tone
from app.models.template import Template

router = APIRouter(prefix="/api/templates", tags=["templates"])


class TemplateIn(BaseModel):
    name: str
    category: TemplateCategory
    stage: Optional[ClientStage] = None
    subject: str
    body: str
    tone: Tone = Tone.POLITE_PROFESSIONAL
    priority: str = "MEDIUM"
    conditions: str = ""
    variables: str = ""
    source: str = "Business Follow-Up Workflow"
    active: bool = True


class TemplateOut(TemplateIn):
    id: int

    class Config:
        from_attributes = True


@router.get("", response_model=List[TemplateOut])
def list_templates(
    db: Session = Depends(get_db),
    category: Optional[TemplateCategory] = None,
    stage: Optional[ClientStage] = None,
    tone: Optional[Tone] = None,
    search: Optional[str] = None,
):
    q = db.query(Template)
    if category:
        q = q.filter(Template.category == category)
    if stage:
        q = q.filter(Template.stage == stage)
    if tone:
        q = q.filter(Template.tone == tone)
    if search:
        q = q.filter(Template.name.ilike(f"%{search}%"))
    return q.order_by(Template.category).all()


@router.get("/{template_id}", response_model=TemplateOut)
def get_template(template_id: int, db: Session = Depends(get_db)):
    t = db.get(Template, template_id)
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    return t


@router.post("", response_model=TemplateOut)
def create_template(payload: TemplateIn, db: Session = Depends(get_db)):
    t = Template(**payload.model_dump())
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@router.put("/{template_id}", response_model=TemplateOut)
def update_template(template_id: int, payload: TemplateIn, db: Session = Depends(get_db)):
    t = db.get(Template, template_id)
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    for field, value in payload.model_dump().items():
        setattr(t, field, value)
    db.commit()
    db.refresh(t)
    return t
