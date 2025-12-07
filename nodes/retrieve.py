import logging

log = logging.getLogger(__name__)

def run_retrieve(state: dict, tools: dict) -> dict:
    invoice = state.get("input_invoice", {})
    atlas = tools.get("atlas")

    pos_resp = atlas.call("fetch_po", invoice)
    grn_resp = atlas.call("fetch_grn", invoice)

    state["RETRIEVE"] = {
        "matched_pos": pos_resp.get("pos", []),
        "matched_grns": grn_resp.get("grns", [])
    }

    msg = f"RETRIEVE: {len(state['RETRIEVE']['matched_pos'])} POs, {len(state['RETRIEVE']['matched_grns'])} GRNs"
    state.setdefault("logs", []).append(msg)
    log.info(msg)
    return state
