from utils.bigtool import BigtoolPicker
import logging
log = logging.getLogger(__name__)

def run_understand(state: dict, tools: dict) -> dict:
    invoice = state["input_invoice"]

    ocr_tool = BigtoolPicker.select(
        "ocr",
        context={"invoice_id": invoice.get("invoice_id")},
        pool_hint=["google_vision", "tesseract", "aws_textract"]
    )

    state.setdefault("logs", []).append(f"UNDERSTAND: selected OCR tool: {ocr_tool}")
    log.info(f"OCR tool selected: {ocr_tool}")

    atlas = tools["atlas"]
    ocr_out = atlas.call(
        "ocr_extract",
        {"attachments": invoice.get("attachments", []), "tool": ocr_tool}
    )

    common = tools["common"]
    parse_out = common.call(
        "parse_line_items",
        {"extracted_text": ocr_out.get("extracted_text"), "line_items": invoice.get("line_items", [])}
    )

    state["UNDERSTAND"] = {
        "ocr_tool": ocr_tool,
        "ocr_output": ocr_out,
        "parsed_invoice": parse_out
    }

    state.setdefault("logs", []).append("UNDERSTAND: OCR & parse complete")
    return state
