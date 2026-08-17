def _create_client(client, **overrides):
    payload = {
        "first_name": "Test",
        "last_name": "Client",
        "company_name": "Test Co",
        "email": "test.client@example.com",
        "current_stage": "NEW_LEAD",
    }
    payload.update(overrides)
    return client.post("/api/clients", json=payload)


def test_create_client(client):
    resp = _create_client(client)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "test.client@example.com"
    assert data["current_stage"] == "NEW_LEAD"


def test_get_client(client):
    created = _create_client(client).json()
    resp = client.get(f"/api/clients/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


def test_get_missing_client_404(client):
    resp = client.get("/api/clients/9999")
    assert resp.status_code == 404


def test_update_client(client):
    created = _create_client(client).json()
    resp = client.put(f"/api/clients/{created['id']}", json={"current_stage": "INTERESTED"})
    assert resp.status_code == 200
    assert resp.json()["current_stage"] == "INTERESTED"


def test_delete_client(client):
    created = _create_client(client).json()
    resp = client.delete(f"/api/clients/{created['id']}")
    assert resp.status_code == 200
    assert client.get(f"/api/clients/{created['id']}").status_code == 404


def test_list_clients_filter_by_stage(client):
    _create_client(client, email="a@example.com", current_stage="NEW_LEAD")
    _create_client(client, email="b@example.com", current_stage="DECLINED")
    resp = client.get("/api/clients", params={"stage": "DECLINED"})
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert results[0]["email"] == "b@example.com"


def test_csv_import_creates_clients(client):
    csv_content = (
        "name,company,email,phone,stage,notes\n"
        "Jordan Blake,Acme Inc,jordan.blake@example.com,555-0100,NEW_LEAD,First contact\n"
    )
    files = {"file": ("clients.csv", csv_content, "text/csv")}
    resp = client.post("/api/clients/import", files=files)
    assert resp.status_code == 200
    body = resp.json()
    assert body["created"] == 1
    assert body["errors"] == []


def test_csv_import_reports_missing_required_field(client):
    csv_content = "name,company,email\nNo Email Here,Acme,\n"
    files = {"file": ("clients.csv", csv_content, "text/csv")}
    resp = client.post("/api/clients/import", files=files)
    assert resp.status_code == 200
    body = resp.json()
    assert body["created"] == 0
    assert len(body["errors"]) == 1
