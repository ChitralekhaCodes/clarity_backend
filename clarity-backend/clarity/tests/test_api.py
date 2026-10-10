import os, tempfile
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(tempfile.mkdtemp(), "test.db")
from fastapi.testclient import TestClient
from app.main import app
from app.services import calculate_co2e, status_for


def test_calculation_and_status():
    assert calculate_co2e(100, 0.82) == 82.0
    assert status_for(50, 100)[1] == "ok"
    assert status_for(85, 100)[1] == "warning"
    assert status_for(101, 100)[1] == "exceeded"


def test_full_workflow():
    with TestClient(app) as c:
        r = c.post("/api/auth/register", json={"name": "Test", "email": "t@x.com", "password": "secret1"})
        assert r.status_code == 201
        h = {"Authorization": "Bearer " + r.json()["token"]}
        assert c.post("/api/auth/register", json={"name": "Test", "email": "t@x.com", "password": "secret1"}).status_code == 409
        assert c.get("/api/activities").status_code == 401

        a = c.post("/api/activities", headers=h, json={"activity_type": "electricity_grid", "quantity": 200})
        assert a.status_code == 201 and a.json()["co2e_kg"] == 164.0
        assert c.post("/api/activities", headers=h, json={"activity_type": "nope", "quantity": 1}).status_code == 404
        assert c.post("/api/activities", headers=h, json={"activity_type": "fuel_petrol", "quantity": -5}).status_code == 422

        d = c.get("/api/dashboard", headers=h).json()
        assert d["total_kg"] == 164.0
        elec = next(t for t in d["targets"] if t["category"] == "electricity")
        assert elec["status"] == "exceeded"          # 164 > system limit 100
        assert d["recommendations"] and d["alerts"]

        assert c.put("/api/targets", headers=h, json={"category": "electricity", "limit_kg": 500}).status_code == 200
        d = c.get("/api/dashboard", headers=h).json()
        assert next(t for t in d["targets"] if t["category"] == "electricity")["status"] == "ok"
        assert "TOTAL" in c.get("/api/report/csv", headers=h).text


def test_admin_factor_versioning():
    with TestClient(app) as c:
        tok = c.post("/api/auth/login", json={"email": "admin@clarity.local", "password": "admin123"}).json()["token"]
        h = {"Authorization": "Bearer " + tok}
        f = next(x for x in c.get("/api/admin/factors", headers=h).json() if x["activity_type"] == "fuel_petrol")
        u = c.put(f"/api/admin/factors/{f['id']}", headers=h, json={"factor_kg_per_unit": 2.5}).json()
        assert u["version"] == f["version"] + 1
        user = c.post("/api/auth/register", json={"name": "User", "email": "u@x.com", "password": "secret1"}).json()
        uh = {"Authorization": "Bearer " + user["token"]}
        assert c.get("/api/admin/factors", headers=uh).status_code == 403
