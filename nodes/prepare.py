from utils.bigtool import BigtoolPicker
import logging
log = logging.getLogger(__name__)

def run_prepare(state: dict, tools: dict) -> dict:
    invoice = state["input_invoice"]
    common = tools["common"]
    atlas = tools["atlas"]

    norm = common.call("normalize_vendor", {"vendor_name": invoice.get("vendor_name")})

    state.setdefault("logs", []).append(f"PREPARE: normalized vendor -> {norm.get('normalized_name')}")

    enrich_tool = BigtoolPicker.select(
        "enrichment",
        context={"invoice_id": invoice.get("invoice_id")},
        pool_hint=["clearbit", "people_data_labs", "vendor_db"]
    )

    enrich_out = atlas.call(
        "enrich_vendor",
        {"vendor_name": invoice.get("vendor_name"), "tool": enrich_tool}
    )

    flags = common.call("compute_flags", {"vendor_tax_id": invoice.get("vendor_tax_id")})

    state["PREPARE"] = {
        "vendor_profile": {
            **norm,
            "tax_id": invoice.get("vendor_tax_id"),
            "enrichment_meta": enrich_out.get("enrichment_meta")
        },
        "normalized_invoice": {
            "amount": invoice.get("amount"),
            "currency": invoice.get("currency"),
            "line_items": invoice.get("line_items")
        },
        "flags": flags
    }

    state.setdefault("logs", []).append("PREPARE: enrichment & flags computed")
    return state
