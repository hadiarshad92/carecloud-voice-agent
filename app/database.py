import sqlite3
import json
from datetime import datetime, timezone
from uuid import uuid4
from app.models import PatientCreate, PatientUpdate

DB_FILE = "patients.db"

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                patient_id TEXT PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                date_of_birth TEXT NOT NULL,
                sex TEXT NOT NULL,
                phone_number TEXT NOT NULL,
                email TEXT,
                address_line_1 TEXT NOT NULL,
                address_line_2 TEXT,
                city TEXT NOT NULL,
                state TEXT NOT NULL,
                zip_code TEXT NOT NULL,
                insurance_provider TEXT,
                insurance_member_id TEXT,
                preferred_language TEXT DEFAULT 'English',
                emergency_contact_name TEXT,
                emergency_contact_phone TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                deleted_at TEXT
            )
        """)
        conn.commit()

def create_patient(patient: PatientCreate) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    patient_id = str(uuid4())
    data = patient.model_dump()
    data["patient_id"] = patient_id
    data["created_at"] = now
    data["updated_at"] = now
    data["deleted_at"] = None

    with get_db() as conn:
        conn.execute("""
            INSERT INTO patients (
                patient_id, first_name, last_name, date_of_birth, sex, phone_number,
                email, address_line_1, address_line_2, city, state, zip_code,
                insurance_provider, insurance_member_id, preferred_language,
                emergency_contact_name, emergency_contact_phone, created_at, updated_at, deleted_at
            ) VALUES (
                :patient_id, :first_name, :last_name, :date_of_birth, :sex, :phone_number,
                :email, :address_line_1, :address_line_2, :city, :state, :zip_code,
                :insurance_provider, :insurance_member_id, :preferred_language,
                :emergency_contact_name, :emergency_contact_phone, :created_at, :updated_at, :deleted_at
            )
        """, data)
        conn.commit()
    return data

def list_patients(last_name=None, date_of_birth=None, phone_number=None) -> list:
    query = "SELECT * FROM patients WHERE deleted_at IS NULL"
    params = []
    if last_name:
        query += " AND lower(last_name) = lower(?)"
        params.append(last_name)
    if date_of_birth:
        query += " AND date_of_birth = ?"
        params.append(date_of_birth)
    if phone_number:
        query += " AND phone_number = ?"
        params.append(phone_number)

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]

def get_patient_by_id(patient_id: str) -> Optional[dict]:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM patients WHERE patient_id = ? AND deleted_at IS NULL", (patient_id,)).fetchone()
        return dict(row) if row else None

def get_patient_by_phone(phone_number: str) -> Optional[dict]:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM patients WHERE phone_number = ? AND deleted_at IS NULL", (phone_number,)).fetchone()
        return dict(row) if row else None

def update_patient(patient_id: str, update_data: PatientUpdate) -> Optional[dict]:
    existing = get_patient_by_id(patient_id)
    if not existing:
        return None
    updates = {k: v for k, v in update_data.model_dump().items() if v is not None}
    if not updates:
        return existing
    
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    set_clause = ", ".join([f"{k} = :{k}" for k in updates.keys()])
    updates["patient_id"] = patient_id

    with get_db() as conn:
        conn.execute(f"UPDATE patients SET {set_clause} WHERE patient_id = :patient_id", updates)
        conn.commit()
    return get_patient_by_id(patient_id)

def soft_delete_patient(patient_id: str) -> bool:
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        cursor = conn.execute("UPDATE patients SET deleted_at = ? WHERE patient_id = ? AND deleted_at IS NULL", (now, patient_id))
        conn.commit()
        return cursor.rowcount > 0