import logging
import uuid
from utils.db import save_checkpoint

log = logging.getLogger(__name__)

def run_checkpoint(state: dict, tools: dict) -> dict:
    checkpoint_id = str(uuid.uuid4())
    state["CHECKPOINT_HITL"] = {"checkpoint_id": checkpoint_id, "paused_reason": None}

    save_checkpoint(checkpoint_id, state)
    msg = f"CHECKPOINT_HITL: created checkpoint {checkpoint_id}"
    state.setdefault("logs", []).append(msg)
    log.info(msg)
    return state
