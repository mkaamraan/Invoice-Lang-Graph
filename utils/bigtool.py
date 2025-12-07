import random
from typing import List, Dict

class BigtoolPicker:
    @staticmethod
    def select(capability: str, context: Dict = None, pool_hint: List[str] = None) -> str:
        """
        Select a tool implementation for a given capability.

        Selection strategy:
          - If pool_hint provided, use it.
          - If context contains invoice_id, pick deterministically using its hash.
          - Else pick randomly.
        """
        pool = pool_hint or []
        if not pool:
            default = {
                "ocr": ["tesseract", "google_vision", "aws_textract"],
                "enrichment": ["clearbit", "people_data_labs", "vendor_db"],
                "erp_connector": ["mock_erp", "netsuite", "sap_sandbox"],
                "db": ["sqlite", "postgres"],
                "email": ["sendgrid", "ses"]
            }
            pool = default.get(capability, ["mock_tool"])
        if context and context.get("invoice_id"):
            idx = abs(hash(context["invoice_id"])) % len(pool)
            return pool[idx]
        return random.choice(pool)
