from datetime import date, datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, EmailStr, Field, field_validator
import re

class SexEnum(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"
    DECLINE = "Decline to Answer"

US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", 
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", 
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", 
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", 
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
}

class PatientBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    date_of_birth: str  # YYYY-MM-DD or MM/DD/YYYY
    sex: SexEnum
    phone_number: str
    email: Optional[EmailStr] = None
    address_line_1: str
    address_line_2: Optional[str] = None
    city: str = Field(..., min_length=1, max_length=100)
    state: str
    zip_code: str
    insurance_provider: Optional[str] = None
    insurance_member_id: Optional[str] = None
    preferred_language: Optional[str] = "English"
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

    @field_validator("phone_number", "emergency_contact_phone")
    def validate_phone(cls, v):
        if v is None:
            return v
        cleaned = re.sub(r"\D", "", v)
        if len(cleaned) != 10:
            raise ValueError("Phone number must be a valid 10-digit U.S. number.")
        return cleaned

    @field_validator("state")
    def validate_state(cls, v):
        if v.upper() not in US_STATES:
            raise ValueError("State must be a valid 2-letter U.S. abbreviation.")
        return v.upper()

    @field_validator("zip_code")
    def validate_zip(cls, v):
        if not re.match(r"^\d{5}(-\d{4})?$", v):
            raise ValueError("ZIP code must be 5 digits or ZIP+4 format.")
        return v

    @field_validator("date_of_birth")
    def validate_dob(cls, v):
        try:
            if "/" in v:
                m, d, y = map(int, v.split("/"))
                dob = date(y, m, d)
            else:
                dob = date.fromisoformat(v)
            if dob > date.today():
                raise ValueError("Date of birth cannot be in the future.")
            return dob.isoformat()
        except Exception:
            raise ValueError("Invalid date format. Use MM/DD/YYYY or YYYY-MM-DD.")

class PatientCreate(PatientBase):
    pass

class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    sex: Optional[SexEnum] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_member_id: Optional[str] = None
    preferred_language: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

class PatientResponse(PatientBase):
    patient_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

class EnvelopeResponse(BaseModel):
    data: Optional[dict | list] = None
    error: Optional[str] = None