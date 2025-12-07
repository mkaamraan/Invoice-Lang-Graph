def run_complete(state: dict, tools: dict) -> dict:
    final_payload = {
        "invoice_id": state["input_invoice"].get("invoice_id"),
        "status": "COMPLETED",
        "amount": state["input_invoice"].get("amount"),
        "audit": state.get("logs", [])
    }

    state["COMPLETE"] = {
        "final_payload": final_payload,
        "audit_log": state.get("logs", [])
    }

    state.setdefault("logs", []).append("COMPLETE: workflow finished")
    state["status"] = "COMPLETED"
    return state
