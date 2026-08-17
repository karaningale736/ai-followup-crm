from datetime import datetime, timedelta


def _create_client(client, **overrides):
    payload = {
        "first_name": "Rahul", "last_name": "Sharma", "company_name": "Acme Corp",
        "email": "rahul.sharma@example.com", "current_stage": "AGREEMENT_SENT",
    }
    payload.update(overrides)
    return client.post("/api/clients", json=payload).json()


def test_analyze_endpoint_returns_decision(client):
    c = _create_client(client)
    resp = client.post("/api/followups/analyze", json={"client_id": c["id"]})
    assert resp.status_code == 200
    body = resp.json()
    assert "recommended_action" in body
    assert "priority" in body


def test_analyze_missing_client_404(client):
    resp = client.post("/api/followups/analyze", json={"client_id": 99999})
    assert resp.status_code == 404


def test_template_crud(client):
    payload = {
        "name": "Test Template",
        "category": "FOLLOW_UP_1",
        "subject": "Hi {client_first_name}",
        "body": "Body referencing {company_name}.",
        "tone": "POLITE_PROFESSIONAL",
    }
    created = client.post("/api/templates", json=payload).json()
    assert created["id"] is not None

    listed = client.get("/api/templates", params={"category": "FOLLOW_UP_1"}).json()
    assert any(t["id"] == created["id"] for t in listed)

    updated = client.put(f"/api/templates/{created['id']}", json={**payload, "active": False}).json()
    assert updated["active"] is False


def test_generate_email_uses_active_template(client):
    c = _create_client(client, current_stage="NEW_LEAD",
                        last_contact_date=(datetime.utcnow() - timedelta(days=3)).isoformat())
    client.put(f"/api/clients/{c['id']}", json={
        "last_contact_date": (datetime.utcnow() - timedelta(days=3)).isoformat()
    })
    client.post("/api/templates", json={
        "name": "FU1", "category": "FOLLOW_UP_1", "subject": "Hi {client_first_name}",
        "body": "Checking in about {feature_title}.", "tone": "POLITE_PROFESSIONAL",
    })
    resp = client.post("/api/followups/generate", json={"client_id": c["id"]})
    assert resp.status_code == 200
    body = resp.json()
    assert "Rahul" in body["subject"] or "[MISSING" not in body["subject"]


def test_dashboard_counts(client):
    _create_client(client, email="one@example.com", current_stage="DECLINED")
    _create_client(client, email="two@example.com", current_stage="NEW_LEAD")
    resp = client.get("/api/dashboard")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_clients"] == 2
    assert body["declined_clients"] == 1


def test_agreement_create_updates_client_stage(client):
    c = _create_client(client, current_stage="NEW_LEAD")
    resp = client.post("/api/agreements", json={"client_id": c["id"], "status": "SENT"})
    assert resp.status_code == 200
    updated_client = client.get(f"/api/clients/{c['id']}").json()
    assert updated_client["current_stage"] == "AGREEMENT_SENT"


def test_agreement_signed_stops_reminders(client):
    c = _create_client(client, current_stage="AGREEMENT_SENT")
    agreement = client.post("/api/agreements", json={"client_id": c["id"], "status": "SENT"}).json()
    client.put(f"/api/agreements/{agreement['id']}", json={"status": "SIGNED"})

    decision = client.post("/api/followups/analyze", json={"client_id": c["id"]}).json()
    assert decision["is_due"] is False


def test_meeting_create_and_update(client):
    c = _create_client(client, current_stage="MEETING_REQUESTED")
    meeting = client.post("/api/meetings", json={"client_id": c["id"], "status": "REQUESTED"}).json()
    resp = client.put(f"/api/meetings/{meeting['id']}", json={"status": "SCHEDULED"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "SCHEDULED"


def test_email_send_updates_client_tracking(client):
    c = _create_client(client, current_stage="NEW_LEAD")
    resp = client.post("/api/emails/send", json={
        "client_id": c["id"], "subject": "Hi", "body": "Test body", "force_mock": True,
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "MOCK_SENT"

    updated = client.get(f"/api/clients/{c['id']}").json()
    assert updated["followup_count"] == 1
    assert updated["last_contact_date"] is not None


def test_inbound_email_sync_creates_reply_notification(client, monkeypatch):
    c = _create_client(client, email="client@example.com", current_stage="NEW_LEAD")

    class FakeInboxMessage:
        def __init__(self):
            self.from_email = "client@example.com"
            self.subject = "Interested in your offer"
            self.body = "Hi, I would like to know the pricing and next step. Please reply."
            self.message_id = "msg-123"

    monkeypatch.setattr(
        "app.services.inbox_monitor.fetch_incoming_messages",
        lambda config=None: [FakeInboxMessage()],
    )

    resp = client.post("/api/emails/inbox/sync", json={
        "imap_host": "imap.gmail.com",
        "imap_port": 993,
        "username": "me@gmail.com",
        "password": "secret",
        "use_ssl": True,
        "mailbox": "INBOX",
    })
    assert resp.status_code == 200
    payload = resp.json()
    assert payload[0]["direction"] == "INBOUND"
    assert payload[0]["status"] == "REPLY_REQUIRED"

    notifications = client.get("/api/emails/inbox/notifications").json()
    assert len(notifications) == 1
    assert notifications[0]["subject"] == "Interested in your offer"


def test_response_classifier_endpoint(client):
    c = _create_client(client, current_stage="AGREEMENT_SENT")
    resp = client.post("/api/responses/classify", json={
        "client_id": c["id"], "message_text": "We would like to sign as soon as possible.",
    })
    assert resp.status_code == 200
    assert resp.json()["classification"] == "READY_TO_SIGN"


def test_auth_register_login_and_me(client):
    register = client.post("/api/auth/register", json={
        "name": "Ana Admin",
        "email": "ana@example.com",
        "password": "StrongPass123!",
        "role": "ADMIN",
    })
    assert register.status_code == 200, register.text
    body = register.json()
    assert body["email"] == "ana@example.com"

    login = client.post("/api/auth/login", json={
        "email": "ana@example.com",
        "password": "StrongPass123!",
    })
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    assert token

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "ana@example.com"
    assert me.json()["role"] == "ADMIN"


def test_app_settings_support_postgres_url(monkeypatch):
    from app.core.config import Settings

    monkeypatch.setenv("DATABASE_URL", "postgresql://crm:crm@db:5432/crm")
    settings = Settings()
    assert settings.database_url.startswith("postgresql://")
