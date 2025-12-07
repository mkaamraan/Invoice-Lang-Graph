import logging
log = logging.getLogger(__name__)

def run_match(state: dict, tools: dict, match_threshold: float) -> dict:
    invoice = state["input_invoice"]
    pos = state.get("RETRIEVE", {}).get("matched_pos", [])

    match_score = 0.0

    if pos:
        po = pos[0]
        inv_amt = invoice.get("amount", 0)
        po_amt = po.get("amount", 0)

        if po_amt == 0 and inv_amt == 0:
            match_score = 1.0
        else:
            diff = abs(inv_amt - po_amt)
            avg = max((inv_amt + po_amt) / 2.0, 1e-6)
            match_score = max(0.0, 1.0 - (diff / avg))
    else:
        match_score = 0.0

    match_result = "MATCHED" if match_score >= match_threshold else "FAILED"

    state["MATCH_TWO_WAY"] = {
        "match_score": match_score,
        "match_result": match_result
    }

    state.setdefault("logs", []).append(f"MATCH_TWO_WAY: score={match_score:.3f}, result={match_result}")
    return state
