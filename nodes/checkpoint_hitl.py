from utils.db import save_checkpoint
import logging
log = logging.getLogger(__name__)

def run_checkpoint(state: dict, tools: dict) -> dict:
    invoice = state["input_invoice"]
    match_result = state.get("MATCH_TWO_WAY", {}).get("match_result")

    if match_result == "FAILED":
        checkpoint_id = save_checkpoint(invoice.get("invoice_id"), state, status="PAUSED")
        review_url = f"/ui/reviewer.html?checkpoint_id={checkpoint_id}"

        state["CHECKPOINT_HITL"] = {
            "checkpoint_id": checkpoint_id,
            "review_url": review_url,
            "paused_reason": "MATCH_FAILED"
        }

        state.setdefault("logs", []).append(f"CHECKPOINT_HITL: checkpoint created {checkpoint_id}")
        state["paused"] = True
    else:
        state["CHECKPOINT_HITL"] = {"checkpoint_id": None, "review_url": None}

    return state
