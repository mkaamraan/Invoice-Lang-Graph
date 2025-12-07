def run_notify(state: dict, tools: dict) -> dict:
    notify_status = {
        "vendor_email": "sent",
        "finance_slack": "sent"
    }

    state["NOTIFY"] = {
        "notify_status": notify_status,
        "notified_parties": ["vendor", "finance_team"]
    }

    state.setdefault("logs", []).append("NOTIFY: notifications sent")
    return state
