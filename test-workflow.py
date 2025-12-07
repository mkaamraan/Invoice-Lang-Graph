import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def start_workflow(invoice_file="sample_invoice.json"):
    with open(invoice_file) as f:
        invoice = json.load(f)
    r = requests.post(f"{BASE_URL}/start-workflow", json=invoice)
    data = r.json()
    print("\n=== Start Workflow Response ===")
    print(json.dumps(data, indent=2))
    return data

def get_pending_hitl():
    r = requests.get(f"{BASE_URL}/human-review/pending")
    data = r.json()
    print("\n=== Pending HITL Items ===")
    print(json.dumps(data, indent=2))
    return data

def submit_hitl_decision(checkpoint_id, decision="ACCEPT", notes="Auto-approved by script"):
    payload = {
        "checkpoint_id": checkpoint_id,
        "decision": decision,
        "notes": notes
    }
    r = requests.post(f"{BASE_URL}/human-review/decision", json=payload)
    data = r.json()
    print(f"\n=== HITL Decision Response (checkpoint {checkpoint_id}) ===")
    print(json.dumps(data, indent=2))
    return data

def run_full_workflow():
    # Step 1: Start workflow
    workflow = start_workflow()

    # Step 2: Check for HITL
    time.sleep(1)  # wait a bit for workflow nodes to process
    pending = get_pending_hitl()

    # Step 3: Auto-approve all pending HITL items
    for item in pending:
        checkpoint_id = item.get("checkpoint_id")
        if checkpoint_id:
            submit_hitl_decision(checkpoint_id)

    print("\n✅ Workflow test completed!")

if __name__ == "__main__":
    run_full_workflow()
