import logging

log = logging.getLogger(__name__)

def run_understand(state: dict, tools: dict) -> dict:
    invoice = state.get("input_invoice", {})
    atlas = tools.get("atlas")

    # OCR / Text extraction
    ocr_resp = atlas.call("ocr_extract", {"attachments": invoice.get("attachments", [])})
    invoice_text = ocr_resp.get("extracted_text", "")

    # Parse line items
    common = tools.get("common")
    parsed_resp = common.call("parse_line_items", {**invoice, "extracted_text": invoice_text})

    state["UNDERSTAND"] = {
        "parsed_invoice": parsed_resp
    }

    msg = f"UNDERSTAND: parsed {len(parsed_resp.get('parsed_line_items', []))} line items"
    state.setdefault("logs", []).append(msg)
    log.info(msg)
    return state
