from utils.bigtool import BigtoolPicker
import logging
log = logging.getLogger(__name__)

def run_retrieve(state: dict, tools: dict) -> dict:
    invoice = state["input_invoice"]
    atlas = tools["atlas"]

    erp_tool = BigtoolPicker.select(
        "erp_connector",
        context={"invoice_id": invoice.get("invoice_id")},
        pool_hint=["mock_erp", "netsuite", "sap_sandbox"]
    )

    pos = atlas.call(
        "fetch_po",
        {"invoice_id": invoice.get("invoice_id"), "amount": invoice.get("amount"), "tool": erp_tool}
    ).get("pos", [])

    grns = atlas.call(
        "fetch_grn",
        {"invoice_id": invoice.get("invoice_id"), "tool": erp_tool}
    ).get("grns", [])

    history = atlas.call("fetch_history", {"vendor_name": invoice.get("vendor_name")}).get("history", [])

    state["RETRIEVE"] = {
        "matched_pos": pos,
        "matched_grns": grns,
        "history": history,
        "erp_tool": erp_tool
    }

    state.setdefault("logs", []).append("RETRIEVE: ERP fetch done")
    return state
