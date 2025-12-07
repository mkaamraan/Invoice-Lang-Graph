import json
import logging
import uvicorn
import webbrowser
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional
from utils.db import init_db, get_pending_checkpoints, get_checkpoint, update_checkpoint, save_checkpoint
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

# Load workflow config
with open("workflow.json") as f:
    WORKFLOW = json.load(f)

app = FastAPI()
init_db()
app.mount("/ui", StaticFiles(directory="ui"), name="ui")

# Tool clients
common_client = CommonClient()
atlas_client = AtlasClient()
TOOLS = {"common": common_client, "atlas": atlas_client}

# ----------------------------------------------------------
# WORKFLOW PIPELINE
# ----------------------------------------------------------

def execute_workflow(input_invoice: dict):
    state = {
        "input_invoice": input_invoice,
        "logs": [],
        "status": "RUNNING",
        "paused": False
    }

    # Pipeline
    state = run_intake(state, TOOLS)
    state = run_understand(state, TOOLS)
    state = run_prepare(state, TOOLS)
    state = run_retrieve(state, TOOLS)
    state = run_match(state, TOOLS, match_threshold=WORKFLOW["config"].get("match_threshold", 0.8))

    # Build invoice metadata for reviewer
    inv = input_invoice.copy()
    inv["matched_pos"] = state.get("RETRIEVE", {}).get("matched_pos", [])
    inv["matched_grns"] = state.get("RETRIEVE", {}).get("matched_grns", [])

    if "line_items" not in inv and "parsed_invoice" in state.get("UNDERSTAND", {}):
        inv["line_items"] = state["UNDERSTAND"]["parsed_invoice"].get("parsed_line_items", [])

    # Risk score
    prepare_flags = state.get("PREPARE", {}).get("flags")
    inv["risk_score"] = prepare_flags.get("risk_score") if isinstance(prepare_flags, dict) else None

    # ---- HITL Node ----
    state = run_checkpoint(state, TOOLS)

    if "CHECKPOINT_HITL" in state:
        checkpoint_id = state["CHECKPOINT_HITL"].get("checkpoint_id")
        state["CHECKPOINT_HITL"]["invoice_metadata"] = inv

        # Determine HOLD reasons
        total_po_amount = sum([po.get("amount", 0) for po in inv.get("matched_pos", [])])
        amount_mismatch = (total_po_amount != inv.get("amount", 0))
        missing_fields = state.get("INTAKE", {}).get("missing_fields", [])
        unmatched_pos = (len(inv.get("matched_pos", [])) == 0)

        reasons = []
        if amount_mismatch:
            reasons.append(f"Amount mismatch: invoice {inv.get('amount')} vs PO total {total_po_amount}")
        if unmatched_pos:
            reasons.append("No matched POs found")
        if missing_fields:
            reasons.append(f"Missing fields: {', '.join(missing_fields)}")

        # Only pause if real reasons exist
        if reasons:
            state["paused"] = True
            state["status"] = "PAUSED"
            state["CHECKPOINT_HITL"]["paused_reason"] = "; ".join(reasons)

            # Save checkpoint
            save_checkpoint(checkpoint_id, state, status="PAUSED", resume_token=None)

            # Open reviewer UI just once
            url = f"http://127.0.0.1:8000/ui/reviewer.html?checkpoint_id={checkpoint_id}"
            logger.info(f"Opening Reviewer UI → {url}")
            try:
                webbrowser.open(url)
            except:
                pass

            return state

        # If no reasons -> continue
        logger.info("No HITL required, continuing workflow")

    # Continue pipeline
    state = run_reconcile(state, TOOLS)
    state = run_approve(state, TOOLS)
    state = run_posting(state, TOOLS)
    state = run_notify(state, TOOLS)
    state = run_complete(state, TOOLS)

    state["status"] = "COMPLETED"
    return state

# ----------------------------------------------------------
# API MODELS
# ----------------------------------------------------------

class StartRequest(BaseModel):
    input_invoice: dict

class DecisionRequest(BaseModel):
    checkpoint_id: str
    decision: str
    notes: Optional[str]
    reviewer_id: str

# ----------------------------------------------------------
# ROUTES
# ----------------------------------------------------------

@app.post("/start-workflow")
def start_workflow(req: StartRequest):
    logger.info("Workflow started via API")
    return execute_workflow(req.input_invoice)


@app.post("/upload-invoice")
async def upload_invoice(file: UploadFile = File(...)):
    if not file.filename.endswith(".json"):
        return {"error": "Only JSON files are allowed"}

    content = await file.read()
    try:
        data = json.loads(content)
    except Exception as e:
        return {"error": f"Invalid JSON: {str(e)}"}

    input_invoice = data.get("input_invoice", data)
    return execute_workflow(input_invoice)


@app.get("/human-review/pending")
def list_pending():
    items = get_pending_checkpoints()
    output = []

    for it in items:
        st = it.get("state", {})
        cp_hitl = st.get("CHECKPOINT_HITL", {})
        inv = cp_hitl.get("invoice_metadata", st.get("input_invoice", {}))

        paused_reason = cp_hitl.get("paused_reason")
        if not paused_reason:
            paused_reason = "Manual review required"

        output.append({
            "checkpoint_id": it.get("checkpoint_id"),
            "invoice_id": inv.get("invoice_id"),
            "vendor_name": inv.get("vendor_name"),
            "amount": inv.get("amount"),
            "currency": inv.get("currency"),
            "invoice_date": inv.get("invoice_date"),
            "line_items": inv.get("line_items", []),
            "matched_pos": inv.get("matched_pos", []),
            "matched_grns": inv.get("matched_grns", []),
            "reason_for_hold": paused_reason,
            "review_url": f"/ui/reviewer.html?checkpoint_id={it.get('checkpoint_id')}",
            "created_at": it.get("created_at"),
            "status": it.get("status", "PAUSED")
        })

    return {"items": output}


@app.post("/human-review/decision")
def decision(req: DecisionRequest):
    cp = get_checkpoint(req.checkpoint_id)
    if not cp:
        raise HTTPException(status_code=404, detail="checkpoint not found")

    if cp.get("status") != "PAUSED":
        raise HTTPException(status_code=400, detail="checkpoint not paused")

    state, status = apply_human_decision(
        req.checkpoint_id, req.decision, req.notes or "", req.reviewer_id
    )

    if status != "ok":
        raise HTTPException(status_code=500, detail="Failed to apply decision")

    # Accept → continue workflow
    if req.decision.upper() == "ACCEPT":
        state = run_reconcile(state, TOOLS)
        state = run_approve(state, TOOLS)
        state = run_posting(state, TOOLS)
        state = run_notify(state, TOOLS)
        state = run_complete(state, TOOLS)
    else:
        state["status"] = "MANUAL_HANDOFF"

    return {
        "next_stage": "RECONCILE" if req.decision.upper() == "ACCEPT" else None,
        "post_decision_logs": state.get("logs", []),
        "final_state": state
    }


@app.get("/api/checkpoint/{checkpoint_id}")
def get_checkpoint_data(checkpoint_id: str):
    cp = get_checkpoint(checkpoint_id)
    if not cp:
        raise HTTPException(status_code=404, detail="checkpoint not found")
    return {"checkpoint_id": checkpoint_id, "state": cp.get("state"), "status": cp.get("status")}


# Serve UI
@app.get("/ui/{filename}", response_class=HTMLResponse)
async def serve_ui(filename: str):
    try:
        with open(f"ui/{filename}", "r", encoding="utf-8") as f:
            return f.read()
    except:
        return HTMLResponse("<h3>404 Not Found</h3>", status_code=404)


# ----------------------------------------------------------
# START SERVER
# ----------------------------------------------------------
if __name__ == "__main__":
    url = "http://127.0.0.1:8000/ui/upload.html"
    try:
        webbrowser.open(url)
    except:
        pass

    uvicorn.run(app, host="0.0.0.0", port=8000)
