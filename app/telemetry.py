import logging
import json
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("telemetry")

def log_call_session(call_sid: str, from_phone: str, summary: str, payload: dict):
    telemetry_record = {
        "call_sid": call_sid,
        "caller_phone": from_phone,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
        "collected_payload": payload
    }
    logger.info(f"CALL_TELEMETRY: {json.dumps(telemetry_record)}")
    
    # Save call telemetry artifact to disk
    with open(f"call_log_{call_sid}.json", "w") as f:
        json.dump(telemetry_record, f, indent=2)