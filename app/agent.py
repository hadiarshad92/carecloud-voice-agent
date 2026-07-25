import os
import json
import logging
from google import genai
from app.database import create_patient, get_patient_by_phone, update_patient
from app.models import PatientCreate, PatientUpdate

logger = logging.getLogger("voice-agent")

SYSTEM_INSTRUCTION = """
You are an expert Patient Intake Coordinator for CareCloud.
Your job is to conversationally collect demographic information to register new patients.

RULES:
1. Conduct a natural, empathetic conversation. Ask 1-2 questions at a time.
2. Mandatory fields to collect: First Name, Last Name, Date of Birth (MM/DD/YYYY), Sex (Male/Female/Other/Decline), Phone Number, Address Line 1, City, State (2-letter code), ZIP Code.
3. Offer optional fields: Once mandatory fields are collected, ask: "I can also collect optional information like your insurance provider, member ID, emergency contact, or preferred language. Would you like to provide any of those?"
4. VALIDATION: If a caller gives an invalid value (e.g. 3-digit phone or future DOB), politely inform them and re-prompt specifically for that field.
5. CONFIRMATION STEP: BEFORE saving, read back ALL collected fields to the user and explicitly ask for confirmation.
6. DUPLICATE CHECK: When you get the phone number, invoke `check_caller_registered`. If registered, ask: "I see a record for [Name]. Would you like to update your details or proceed as new?"
7. Once confirmed, invoke `save_patient_record`.
"""

def get_gemini_client():
    return genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# Tool Functions for Gemini Function Calling
tools_schema = [
    {
        "name": "check_caller_registered",
        "description": "Checks if a patient already exists in the database by phone number.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "phone_number": {"type": "STRING", "description": "10-digit U.S. phone number"}
            },
            "required": ["phone_number"]
        }
    },
    {
        "name": "save_patient_record",
        "description": "Saves or updates the confirmed patient demographic record into the database.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "first_name": {"type": "STRING"},
                "last_name": {"type": "STRING"},
                "date_of_birth": {"type": "STRING"},
                "sex": {"type": "STRING"},
                "phone_number": {"type": "STRING"},
                "address_line_1": {"type": "STRING"},
                "city": {"type": "STRING"},
                "state": {"type": "STRING"},
                "zip_code": {"type": "STRING"},
                "email": {"type": "STRING"},
                "insurance_provider": {"type": "STRING"},
                "insurance_member_id": {"type": "STRING"},
                "emergency_contact_name": {"type": "STRING"},
                "emergency_contact_phone": {"type": "STRING"},
                "existing_patient_id": {"type": "STRING", "description": "Provided only if updating existing patient"}
            },
            "required": ["first_name", "last_name", "date_of_birth", "sex", "phone_number", "address_line_1", "city", "state", "zip_code"]
        }
    }
]

def execute_tool_call(name: str, args: dict) -> dict:
    logger.info(f"Executing tool call: {name} with args {args}")
    if name == "check_caller_registered":
        patient = get_patient_by_phone(args.get("phone_number"))
        if patient:
            return {"exists": True, "patient_id": patient["patient_id"], "first_name": patient["first_name"], "last_name": patient["last_name"]}
        return {"exists": False}

    elif name == "save_patient_record":
        try:
            if args.get("existing_patient_id"):
                updated = update_patient(args["existing_patient_id"], PatientUpdate(**args))
                return {"status": "success", "message": "Patient record updated successfully", "data": updated}
            else:
                created = create_patient(PatientCreate(**args))
                return {"status": "success", "message": "Patient registered successfully", "data": created}
        except Exception as e:
            logger.error(f"Error saving patient: {str(e)}")
            return {"status": "error", "message": str(e)}

    return {"status": "error", "message": "Unknown tool function"}