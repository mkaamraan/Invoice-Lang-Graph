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

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("orchestrator")

# Load workflow configuration
with open("workflow.json") as f:
    WORKFLOW = json.load(f)

app = FastAPI()
init_db()

# Mount UI static files
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
    
    # HITL checkpoint
    state = run_checkpoint(state, TOOLS)
    
    if state.get("paused"):
        checkpoint_id = state["CHECKPOINT_HITL"]["checkpoint_id"]
        url = f"http://127.0.0.1:8000/ui/reviewer.html?checkpoint_id={checkpoint_id}"
        logger.info(f"HITL required! Visit: {url}")
        # Auto-open the reviewer UI in browser for demo purposes
        webbrowser.open(url)
        state["status"] = "PAUSED"
        return state

    # Resume remaining workflow if no HITL pause
    state = run_reconcile(state, TOOLS)
    state = run_approve(state, TOOLS)
    state = run_posting(state, TOOLS)
    state = run_notify(state, TOOLS)
    state = run_complete(state, TOOLS)
    state["status"] = "COMPLETED"
    return state


# Request models
class StartRequest(BaseModel):
    input_invoice: dict


class DecisionRequest(BaseModel):
    checkpoint_id: str
    decision: str  # ACCEPT or REJECT
    notes: Optional[str]
    reviewer_id: str


# API endpoints
@app.post("/start-workflow")
def start_workflow(req: StartRequest):
    logger.info("Start workflow called")
    state = execute_workflow(req.input_invoice)
    return state


@app.get("/human-review/pending")
def list_pending():
    items = get_pending_checkpoints()
    res = []
    for it in items:
        st = it["state"]
        inv = st.get("input_invoice", {})
        res.append({
            "checkpoint_id": it["checkpoint_id"],
            "invoice_id": inv.get("invoice_id"),
            "vendor_name": inv.get("vendor_name"),
            "amount": inv.get("amount"),
            "created_at": it["created_at"],
            "reason_for_hold": st.get("CHECKPOINT_HITL", {}).get("paused_reason"),
            "review_url": f"/ui/reviewer.html?checkpoint_id={it['checkpoint_id']}"
        })
    return {"items": res}


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
    
    if req.decision.upper() == "ACCEPT":
        # Resume workflow after human approval
        state = run_reconcile(state, TOOLS)
        state = run_approve(state, TOOLS)
        state = run_posting(state, TOOLS)
        state = run_notify(state, TOOLS)
        state = run_complete(state, TOOLS)
        return {"resume_token": cp["resume_token"], "next_stage": "RECONCILE", "final_state": state}
    else:
        state["status"] = "MANUAL_HANDOFF"
        return {"resume_token": None, "next_stage": None, "final_state": state}


if __name__ == "__main__":
    logger.info("Starting app at http://127.0.0.1:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
