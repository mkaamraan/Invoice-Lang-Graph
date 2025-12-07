import json
import logging
import uvicorn
import webbrowser
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from utils.db import init_db, get_pending_checkpoints, get_checkpoint
from utils.mcp_router import CommonClient, AtlasClient
from nodes.intake import run_intake
from nodes.understand import run_understand
from nodes.prepare import run_prepare
from nodes.retrieve import run_retrieve
from nodes.match import run_match
from nodes.checkpoint_hitl import run_checkpoint
from nodes.hitl_decision import apply_human_decision
from nodes.reconcile import run_reconcile
from nodes.approve import run_approve
from nodes.posting import run_posting
from nodes.notify import run_notify
from nodes.complete import run_complete
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("orchestrator")

# Load workflow configuration
with open("workflow.json") as f:
    WORKFLOW = json.load(f)

app = FastAPI()
init_db()

# Mount UI directory
app.mount("/ui", StaticFiles(directory="ui"), name="ui")

# Initialize tool clients
common_client = CommonClient()
atlas_client = AtlasClient()
TOOLS = {"common": common_client, "atlas": atlas_client}


def execute_workflow(input_invoice: dict):
    state = {"input_invoice": input_invoice, "logs": [], "status": "RUNNING", "paused": False}

    # Workflow nodes
    state = run_intake(state, TOOLS)
    state = run_understand(state, TOOLS)
    state = run_prepare(state, TOOLS)
    state = run_retrieve(state, TOOLS)
    state = run_match(state, TOOLS, match_threshold=WORKFLOW["config"]["match_threshold"])

    # Add invoice details for HITL UI
    state = run_checkpoint(state, TOOLS)
    if "CHECKPOINT_HITL" in state:
        invoice_meta = input_invoice.copy()
        invoice_meta["matched_pos"] = state.get("RETRIEVE", {}).get("matched_pos", [])
        invoice_meta["matched_grns"] = state.get("RETRIEVE", {}).get("matched_grns", [])
        if "line_items" not in invoice_meta and "parsed_invoice" in state.get("UNDERSTAND", {}):
            invoice_meta["line_items"] = state["UNDERSTAND"]["parsed_invoice"].get("parsed_line_items", [])
        invoice_meta["risk_score"] = state.get("PREPARE", {}).get("flags", {}).get("risk_score")
        state["CHECKPOINT_HITL"]["invoice_metadata"] = invoice_meta

    # Pause for HITL
    if state.get("paused"):
        checkpoint_id = state["CHECKPOINT_HITL"]["checkpoint_id"]
        url = f"http://127.0.0.1:8000/ui/reviewer.html?checkpoint_id={checkpoint_id}"
        logger.info(f"HITL required! Visit: {url}")
        webbrowser.open(url)
        state["status"] = "PAUSED"
        return state

    # Continue workflow if no HITL pause
    state = run_reconcile(state, TOOLS)
    state = run_approve(state, TOOLS)
    state = run_posting(state, TOOLS)
    state = run_notify(state, TOOLS)
    state = run_complete(state, TOOLS)
    state["status"] = "COMPLETED"
    return state


# Request Models
class StartRequest(BaseModel):
    input_invoice: dict


class DecisionRequest(BaseModel):
    checkpoint_id: str
    decision: str  # ACCEPT or REJECT
    notes: Optional[str]
    reviewer_id: str


# Start Workflow
@app.post("/start-workflow")
def start_workflow(req: StartRequest):
    logger.info("Workflow started")
    state = execute_workflow(req.input_invoice)
    return state


# Human Review Pending List
@app.get("/human-review/pending")
def list_pending():
    items = get_pending_checkpoints()
    res = []

    for it in items:
        st = it["state"]
        inv = st.get("input_invoice", {})
        full_invoice = st.get("CHECKPOINT_HITL", {}).get("invoice_metadata", inv)

        res.append({
            "checkpoint_id": it["checkpoint_id"],
            "invoice_id": full_invoice.get("invoice_id"),
            "vendor_name": full_invoice.get("vendor_name"),
            "amount": full_invoice.get("amount"),
            "currency": full_invoice.get("currency"),
            "invoice_date": full_invoice.get("invoice_date"),
            "line_items": full_invoice.get("line_items", []),
            "matched_pos": full_invoice.get("matched_pos", []),
            "matched_grns": full_invoice.get("matched_grns", []),
            "created_at": it["created_at"],
            "reason_for_hold": st.get("CHECKPOINT_HITL", {}).get("paused_reason"),
            "invoice_data": full_invoice,
            "review_url": f"/ui/reviewer.html?checkpoint_id={it['checkpoint_id']}"
        })

    return {"items": res}


# Human Decision
@app.post("/human-review/decision")
def decision(req: DecisionRequest):
    cp = get_checkpoint(req.checkpoint_id)
    if not cp:
        raise HTTPException(status_code=404, detail="checkpoint not found")
    if cp["status"] != "PAUSED":
        raise HTTPException(status_code=400, detail="checkpoint not in PAUSED state")

    state, status = apply_human_decision(req.checkpoint_id, req.decision, req.notes or "", req.reviewer_id)
    if status != "ok":
        raise HTTPException(status_code=500, detail="failed to apply decision")

    if "CHECKPOINT_HITL" in state:
        state["invoice_metadata"] = state["CHECKPOINT_HITL"].get("invoice_metadata")

    # Run post-decision workflow stages only if ACCEPT
    if req.decision.upper() == "ACCEPT":
        state = run_reconcile(state, TOOLS)
        state = run_approve(state, TOOLS)
        state = run_posting(state, TOOLS)
        state = run_notify(state, TOOLS)
        state = run_complete(state, TOOLS)

    else:
        state["status"] = "MANUAL_HANDOFF"

    # Return only post-decision logs
    post_decision_logs = state.get("logs", [])
    return {
        "resume_token": cp.get("resume_token"),
        "next_stage": "RECONCILE" if req.decision.upper() == "ACCEPT" else None,
        "final_state": state,
        "post_decision_logs": post_decision_logs
    }


# Fetch checkpoint for UI
@app.get("/api/checkpoint/{checkpoint_id}")
def get_checkpoint_data(checkpoint_id: str):
    cp = get_checkpoint(checkpoint_id)
    if not cp:
        raise HTTPException(status_code=404, detail="checkpoint not found")

    return {
        "checkpoint_id": checkpoint_id,
        "created_at": cp["created_at"],
        "status": cp["status"],
        "state": cp["state"]
    }


# Serve static HTML UI files
@app.get("/ui/{filename}", response_class=HTMLResponse)
async def serve_ui(filename: str):
    try:
        with open(f"ui/{filename}", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse("<h3>404 - UI File Not Found</h3>", status_code=404)


if __name__ == "__main__":
    url = "http://127.0.0.1:8000/ui/index.html"
    logger.info(f"Starting app at {url}")
    try:
        webbrowser.open(url)
    except Exception as e:
        logger.error(f"Failed to open browser: {e}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
