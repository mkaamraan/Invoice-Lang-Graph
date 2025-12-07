import logging

log = logging.getLogger(__name__)

def run_notify(state: dict, tools: dict) -> dict:
    state["NOTIFY"] = {"notified": True}
    state.setdefault("logs", []).append("NOTIFY: stakeholders notified")
    log.info("NOTIFY executed")
    return state
