def run_posting(state: dict, tools: dict) -> dict:
    atlas = tools["atlas"]
    invoice = state["input_invoice"]

    posted = atlas.call("post_to_erp", {"invoice": invoice})
    scheduled = atlas.call("schedule_payment", {"invoice": invoice})

    state["POSTING"] = {
        "posted": posted.get("posted"),
        "erp_txn_id": posted.get("erp_txn_id"),
        "scheduled_payment_id": scheduled.get("scheduled_payment_id")
    }

    state.setdefault("logs", []).append("POSTING: posted & payment scheduled")
    return state
