import logging

log = logging.getLogger(__name__)

def run_match(state: dict, tools: dict, match_threshold=0.9) -> dict:
    matched_pos = state.get("RETRIEVE", {}).get("matched_pos", [])
    invoice_amount = state.get("input_invoice", {}).get("amount", 0)

    matched = []
    for po in matched_pos:
        po_amount = po.get("amount", 0)
        if po_amount >= invoice_amount * match_threshold:
            matched.append(po)
    state["RETRIEVE"]["matched_pos"] = matched

    msg = f"MATCH: {len(matched)} matched POs after threshold {match_threshold}"
    state.setdefault("logs", []).append(msg)
    log.info(msg)
    return state
