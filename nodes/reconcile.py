def run_reconcile(state: dict, tools: dict) -> dict:
    common = tools["common"]

    acct = common.call(
        "build_accounting_entries",
        {"amount": state["input_invoice"].get("amount")}
    )

    state["RECONCILE"] = {
        "accounting_entries": acct.get("entries"),
        "reconciliation_report": {"status": "ok"}
    }

    state.setdefault("logs", []).append("RECONCILE: accounting entries built")
    return state
