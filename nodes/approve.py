import logging

log = logging.getLogger(__name__)

def run_approve(state: dict, tools: dict) -> dict:
    state["APPROVE"] = {"approved": True}
    state.setdefault("logs", []).append("APPROVE: invoice approved")
    log.info("APPROVE executed")
    return state
