import logging

log = logging.getLogger(__name__)

def run_prepare(state: dict, tools: dict) -> dict:
    invoice = state.get("input_invoice", {})
    common = tools.get("common")

    resp = common.call("compute_flags", invoice)
    state["PREPARE"] = {
        "flags": resp.get("flags", {}),
        "risk_score": resp.get("risk_score", 0)
    }

    msg = f"PREPARE: flags={resp.get('flags', [])}, risk_score={resp.get('risk_score', 0):.2f}"
    state.setdefault("logs", []).append(msg)
    log.info(msg)
    return state
