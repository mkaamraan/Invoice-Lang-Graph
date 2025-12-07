import time
import random
from typing import Any, Dict

class CommonClient:
    def call(self, ability: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        time.sleep(0.05)
        if ability == "normalize_vendor":
            name = payload.get("vendor_name", "")
            return {"normalized_name": name.strip().title()}
        if ability == "compute_flags":
            flags = []
            if not payload.get("vendor_tax_id"):
                flags.append("missing_tax_id")
            return {"flags": flags, "risk_score": random.random()}
        if ability == "parse_line_items":
            return {"parsed_line_items": payload.get("line_items", []),
                    "invoice_text": payload.get("extracted_text", "")}
        if ability == "build_accounting_entries":
            return {"entries": [{"debit": payload.get("amount", 0), "credit": 0}]}
        return {"ok": True, "ability": ability}

class AtlasClient:
    def call(self, ability: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        time.sleep(0.1)
        if ability == "ocr_extract":
            attachments = payload.get("attachments", [])
            text = "OCR TEXT: " + (";".join(attachments) if attachments else "no_attach")
            return {"extracted_text": text}
        if ability == "enrich_vendor":
            return {"enrichment_meta": {"pan": "ABCDE1234F", "gst": "27XXXXX", "credit_score": random.randint(300, 850)}}
        if ability == "fetch_po":
            # return a PO with a different amount to trigger HITL
            return {"pos": [{"po_id": "PO-900", "amount": 10000}]}
        if ability == "fetch_grn":
            return {"grns": []}
        if ability == "fetch_history":
            return {"history": []}
        if ability == "post_to_erp":
            return {"posted": True, "erp_txn_id": "ERP" + str(random.randint(1000, 9999))}
        if ability == "schedule_payment":
            return {"scheduled_payment_id": "PAY" + str(random.randint(1000, 9999))}
        return {"ok": True, "ability": ability}
