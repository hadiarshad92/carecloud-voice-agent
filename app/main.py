import os
import logging
from typing import Optional
from fastapi import FastAPI, Query, HTTPException, Response, Request
from twilio.twiml.voice_response import VoiceResponse, Gather
from dotenv import load_dotenv

from app.database import init_db, list_patients, get_patient_by_id, create_patient, update_patient, soft_delete_patient
from app.models import PatientCreate, PatientUpdate, EnvelopeResponse
from app.agent import get_gemini_client, SYSTEM_INSTRUCTION, tools_schema, execute_tool_call
from app.telemetry import log_call_session

load_dotenv()
init_db()

app = FastAPI(title="CareCloud Patient Registration API", version="1.0.0")
logger = logging.getLogger("main")

# Memory store for active call sessions
call_sessions = {}

@app.on_event("startup")
def startup():
    init_db()
    logger.info("Application started. Database initialized.")

# --- REST API ENDPOINTS ---

@app.get("/patients", response_model=EnvelopeResponse)
def get_patients(
    last_name: Optional[str] = Query(None),
    date_of_birth: Optional[str] = Query(None),
    phone_number: Optional[str] = Query(None)
):
    patients = list_patients(last_name, date_of_birth, phone_number)
    return {"data": patients, "error": None}

@app.get("/patients/{patient_id}", response_model=EnvelopeResponse)
def get_patient(patient_id: str):
    patient = get_patient_by_id(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient record not found")
    return {"data": patient, "error": None}

@app.post("/patients", response_model=EnvelopeResponse, status_code=201)
def add_patient(patient: PatientCreate):
    try:
        created = create_patient(patient)
        return {"data": created, "error": None}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/patients/{patient_id}", response_model=EnvelopeResponse)
def edit_patient(patient_id: str, updates: PatientUpdate):
    updated = update_patient(patient_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Patient record not found")
    return {"data": updated, "error": None}

@app.delete("/patients/{patient_id}", response_model=EnvelopeResponse)
def delete_patient(patient_id: str):
    success = soft_delete_patient(patient_id)
    if not success:
        raise HTTPException(status_code=404, detail="Patient not found or already deleted")
    return {"data": {"message": "Patient record soft-deleted successfully"}, "error": None}

# --- TELEPHONY INBOUND VOICE WEBHOOK ---

@app.post("/voice/inbound")
async def inbound_call(request: Request):
    form_data = await request.form()
    call_sid = form_data.get("CallSid", "unknown")
    caller = form_data.get("From", "")

    # Initialize Gemini session for this call
    client = get_gemini_client()
    chat = client.chats.create(model="gemini-2.5-flash", config={"system_instruction": SYSTEM_INSTRUCTION})
    
    call_sessions[call_sid] = {
        "chat": chat,
        "caller": caller,
        "transcript": []
    }

    # First turn: Gemini greeting
    init_prompt = f"The caller has just connected from phone number {caller}. Greet them professionally and begin patient registration."
    resp = chat.send_message(init_prompt)

    vr = VoiceResponse()
    gather = Gather(input="speech", action=f"/voice/process?call_sid={call_sid}", speechTimeout="auto")
    gather.say(resp.text)
    vr.append(gather)
    return Response(content=str(vr), media_type="application/xml")

@app.post("/voice/process")
async def process_speech(request: Request, call_sid: str):
    form_data = await request.form()
    user_speech = form_data.get("SpeechResult", "")
    
    session = call_sessions.get(call_sid)
    vr = VoiceResponse()

    if not session or not user_speech:
        vr.say("I didn't hear anything. Let's try again.")
        gather = Gather(input="speech", action=f"/voice/process?call_sid={call_sid}", speechTimeout="auto")
        vr.append(gather)
        return Response(content=str(vr), media_type="application/xml")

    chat = session["chat"]
    session["transcript"].append(f"Caller: {user_speech}")

    # Send speech result to Gemini
    response = chat.send_message(user_speech)
    session["transcript"].append(f"Agent: {response.text}")

    # Handle Tool Calls if Gemini triggers a function
    if response.function_calls:
        for fc in response.function_calls:
            result = execute_tool_call(fc.name, fc.args)
            # Feed result back to model
            follow_up = chat.send_message(f"Tool Result ({fc.name}): {json.dumps(result)}")
            response_text = follow_up.text
            if fc.name == "save_patient_record" and result.get("status") == "success":
                log_call_session(call_sid, session["caller"], "Registration Complete", result.get("data"))
                vr.say(response_text)
                vr.say("Thank you for registering with CareCloud. Have a great day!")
                vr.hangup()
                return Response(content=str(vr), media_type="application/xml")
    else:
        response_text = response.text

    gather = Gather(input="speech", action=f"/voice/process?call_sid={call_sid}", speechTimeout="auto")
    gather.say(response_text)
    vr.append(gather)
    return Response(content=str(vr), media_type="application/xml")