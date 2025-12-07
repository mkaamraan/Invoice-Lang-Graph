from utils.db import get_checkpoint, update_checkpoint_status
import logging
log = logging.getLogger(__name__)

def apply_human_decision(checkpoint_id: str, decision: str, notes: str, reviewer_id: str):
    cp = get_checkpoint(checkpoint_id)

    if not cp:
        return None, "checkpoint_not_found"

    state = cp["state"]

    state["HITL_DECISION"] = {
        "human_decision": decision.upper(),
        "reviewer_id": reviewer_id,
        "notes": notes
    }

    update_checkpoint_status(checkpoint_id, "RESOLVED")
    return state, "ok"
