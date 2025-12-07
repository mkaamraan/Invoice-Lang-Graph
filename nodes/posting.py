import logging
from utils.mcp_router import AtlasClient

log = logging.getLogger(__name__)

def run_posting(state: dict, tools: dict) -> dict:
    atlas = tools.get("atlas", AtlasClient())
    invoice = state.get("input_invoice", {})
    resp = atlas.call("post_to_erp", invoice)

    state["POSTING"] = {"erp_txn_id": resp.get("erp_txn_id")}
    state.setdefault("logs", []).append(f"POSTING: posted to ERP {resp.get('erp_txn_id')}")
    log.info("POSTING executed")
    return state
