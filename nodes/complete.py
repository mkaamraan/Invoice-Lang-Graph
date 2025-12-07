import logging

log = logging.getLogger(__name__)

def run_complete(state: dict, tools: dict) -> dict:
    state["COMPLETE"] = {"completed": True}
    state.setdefault("logs", []).append("COMPLETE: workflow finished")
    state["status"] = "COMPLETED"
    log.info("COMPLETE executed")
    return state
