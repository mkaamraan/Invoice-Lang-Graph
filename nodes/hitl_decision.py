import logging
from utils.db import get_checkpoint, save_checkpoint

log = logging.getLogger(__name__)

def apply_human_decision(checkpoint_id: str, decision: str, notes: str, reviewer_id: str):
    cp = get_checkpoint(checkpoint_id)
    if not cp:
        return None, "not_found"

    state = cp["state"]
    state["CHECKPOINT_HITL"]["paused_reason"] = notes
    state["CHECKPOINT_HITL"]["reviewer_id"] = reviewer_id
    state["CHECKPOINT_HITL"]["decision"] = decision.upper()
    state["paused"] = False
    state["status"] = "RESUMED"

    save_checkpoint(checkpoint_id, state, status="RESUMED")
    log.info(f"HITL DECISION: {decision} by {reviewer_id}")
    return state, "ok"
