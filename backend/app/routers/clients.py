import csv
import io
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.enums import ClientStage, Priority
from app.models.client import Client
from app.schemas.client import ClientCreate, ClientUpdate, ClientOut

router = APIRouter(prefix="/api/clients", tags=["clients"])


@router.post("", response_model=ClientOut)
def create_client(payload: ClientCreate, db: Session = Depends(get_db)):
    client = Client(**payload.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.get("", response_model=List[ClientOut])
def list_clients(
    db: Session = Depends(get_db),
    stage: Optional[ClientStage] = None,
    priority: Optional[Priority] = None,
    assigned_manager: Optional[str] = None,
    search: Optional[str] = Query(None, description="Search name, company, email, phone"),
):
    query = db.query(Client)
    if stage:
        query = query.filter(Client.current_stage == stage)
    if priority:
        query = query.filter(Client.priority == priority)
    if assigned_manager:
        query = query.filter(Client.assigned_manager == assigned_manager)
    if search:
        like = f"%{search}%"
        query = query.filter(
            (Client.first_name.ilike(like))
            | (Client.last_name.ilike(like))
            | (Client.company_name.ilike(like))
            | (Client.email.ilike(like))
            | (Client.phone.ilike(like))
        )
    return query.order_by(Client.updated_at.desc()).all()


@router.get("/export")
def export_clients(db: Session = Depends(get_db)):
    clients = db.query(Client).all()
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["name", "company", "email", "phone", "stage", "last_contact_date",
                      "priority", "offer_amount", "currency", "notes"])
    for c in clients:
        writer.writerow([
            c.full_name, c.company_name, c.email, c.phone, c.current_stage.value,
            c.last_contact_date.isoformat() if c.last_contact_date else "",
            c.priority.value, c.offer_amount or "", c.currency, c.notes,
        ])
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=clients_export.csv"},
    )


@router.post("/import")
def import_clients(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = file.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(content))

    required = {"name", "email"}
    errors = []
    created = 0
    preview_rows = []

    for i, row in enumerate(reader, start=2):  # row 1 is header
        row_errors = [f"missing '{f}'" for f in required if not row.get(f)]
        if row_errors:
            errors.append({"row": i, "errors": row_errors})
            continue

        name_parts = row["name"].strip().split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        stage_value = row.get("stage", "NEW_LEAD").strip().upper() or "NEW_LEAD"
        try:
            stage = ClientStage(stage_value)
        except ValueError:
            errors.append({"row": i, "errors": [f"unknown stage '{stage_value}'"]})
            continue

        client = Client(
            first_name=first_name,
            last_name=last_name,
            company_name=row.get("company", ""),
            email=row["email"],
            phone=row.get("phone", ""),
            current_stage=stage,
            client_concern=row.get("notes", ""),
            notes=row.get("notes", ""),
        )
        db.add(client)
        created += 1
        preview_rows.append(row)

    db.commit()
    return {"created": created, "errors": errors}


@router.get("/{client_id}", response_model=ClientOut)
def get_client(client_id: int, db: Session = Depends(get_db)):
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.put("/{client_id}", response_model=ClientOut)
def update_client(client_id: int, payload: ClientUpdate, db: Session = Depends(get_db)):
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(client, field, value)
    client.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(client)
    return client


@router.delete("/{client_id}")
def delete_client(client_id: int, db: Session = Depends(get_db)):
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    db.delete(client)
    db.commit()
    return {"deleted": True}


@router.get("/{client_id}/timeline")
def client_timeline(client_id: int, db: Session = Depends(get_db)):
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    events = []
    events.append({"type": "CLIENT_CREATED", "timestamp": client.created_at})
    for e in client.emails:
        events.append({
            "type": f"EMAIL_{e.direction.value}",
            "timestamp": e.sent_at or e.received_at or e.created_at,
            "subject": e.subject,
            "status": e.status.value,
        })
    for m in client.meetings:
        events.append({"type": f"MEETING_{m.status.value}", "timestamp": m.updated_at, "notes": m.notes})
    for a in client.agreements:
        for label, ts in [("AGREEMENT_SENT", a.sent_at), ("AGREEMENT_OPENED", a.opened_at),
                           ("AGREEMENT_SIGNED", a.signed_at), ("AGREEMENT_DECLINED", a.declined_at)]:
            if ts:
                events.append({"type": label, "timestamp": ts})

    events = [e for e in events if e["timestamp"] is not None]
    events.sort(key=lambda e: e["timestamp"])
    return {"client_id": client_id, "events": events}
