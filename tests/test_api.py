import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import init_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    init_db()

def test_patient_crud_flow():
    # 1. Create Patient
    payload = {
        "first_name": "Jane",
        "last_name": "Doe",
        "date_of_birth": "1992-05-15",
        "sex": "Female",
        "phone_number": "5551234567",
        "address_line_1": "123 Main St",
        "city": "Somerset",
        "state": "NJ",
        "zip_code": "08873"
    }
    res = client.post("/patients", json=payload)
    assert res.status_code == 201
    data = res.json()["data"]
    patient_id = data["patient_id"]
    assert data["first_name"] == "Jane"

    # 2. Query Patient List
    list_res = client.get("/patients?last_name=Doe")
    assert list_res.status_code == 200
    assert len(list_res.json()["data"]) >= 1

    # 3. Soft Delete Patient
    del_res = client.delete(f"/patients/{patient_id}")
    assert del_res.status_code == 200

    # 4. Confirm Soft Deleted
    get_res = client.get(f"/patients/{patient_id}")
    assert get_res.status_code == 404