def run_approve(state: dict, tools: dict) -> dict:
    invoice = state["input_invoice"]
    amt = invoice.get("amount", 0)

    approver_id = None

    if amt < 10000:
        approval_status = "AUTO_APPROVED"
    else:
        approval_status = "ESCALATED"
        approver_id = "manager-001"

    state["APPROVE"] = {
        "approval_status": approval_status,
        "approver_id": approver_id
    }

    state.setdefault("logs", []).append(f"APPROVE: status={approval_status}")
    return state
