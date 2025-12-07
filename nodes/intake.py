from datetime import datetime
import logging
log = logging.getLogger(__name__)

def run_intake(state: dict, tools: dict) -> dict:
    payload = state.get("input_invoice", {})
    required = ["invoice_id", "vendor_name", "amount"]
    missing = [r for r in required if not payload.get(r)]
    validated = (len(missing) == 0)

    raw_id = f"raw_{payload.get('invoice_id', 'noid')}"
    ingest_ts = datetime.utcnow().isoformat()

    state["INTAKE"] = {
        "raw_id": raw_id,
        "ingest_ts": ingest_ts,
        "validated": validated,
        "missing_fields": missing
    }

    msg = f"INTAKE: validated={validated}, raw_id={raw_id}"
    state.setdefault("logs", []).append(msg)
    log.info(msg)

    return state
