AI-Powered Invoice Processing Workflow (with HITL Checkpointing)

This repository contains a complete AI-driven invoice processing workflow, built using a modular multi-stage architecture inspired by LangGraph-style orchestration. It demonstrates real-world workflow automation.

Key Highlights

Modular Multi-Node Architecture: Each stage (INTAKE → UNDERSTAND → PREPARE → RETRIEVE → MATCH → HITL → RECONCILE → APPROVE → POSTING → NOTIFY → COMPLETE) is a separate node, following LangGraph/Temporal workflow patterns.

AI-Assisted Invoice Understanding: OCR simulation, vendor normalization, enrichment, line-item parsing, and risk scoring.

Two-Way PO Matching: Compares invoice vs ERP PO, calculates match score, pauses workflow automatically if threshold not met.

Human-In-The-Loop (HITL) Checkpoints: Workflow pauses on failed matches; reviewers can Accept/Reject via a simple UI (reviewer.html), with automatic workflow resume on acceptance.

ERP Lookups (Simulated): Offline mock ERP integration for PO, GRN, and vendor history lookups.

Complete FastAPI Backend: Endpoints for starting workflow, listing HITL items, submitting reviewer decisions, and accessing reviewer UI.



Key Features:

1. Modular Multi-Node Workflow

Each stage is implemented as a separate file under nodes/:

INTAKE → UNDERSTAND → PREPARE → RETRIEVE → MATCH
→ CHECKPOINT_HITL (Pause Workflow)
→ RECONCILE → APPROVE → POSTING → NOTIFY → COMPLETE

Each Node:

Accepts the workflow state

Performs a specific task

Appends logs

Returns updated state

This pattern follows production workflow engines such as LangGraph, Temporal, Airflow, Step Functions.

2. AI-Assisted Invoice Understanding

The workflow simulates:

OCR extraction

Vendor normalization

Vendor metadata enrichment

Line-item interpretation

Risk flag generation

Smart tool selection (BigTool picker)

3. ERP Lookups (Simulated)

Data retrieval includes:

Purchase Order (PO) lookup

Goods Received Note (GRN) lookup

Vendor payment history

Using a mock ERP client to remain fully offline.

4. Two-Way PO Matching

The workflow computes:

Amount difference

Line-item similarity

Risk scoring

Final match score (0–1)

Threshold configurable in workflow.json.

If score < threshold → workflow PAUSED → HITL required.

5. Human-In-The-Loop (HITL) Checkpointing

If automatic processing fails:

Workflow state is saved into SQLite

A checkpoint ID is created

Reviewer UI allows Accept/Reject with notes

ACCEPT → workflow resumes
REJECT → workflow ends as MANUAL_HANDOFF

6. Workflow Auto-Resume After Approval

After acceptance:

RECONCILE → APPROVE → POSTING → NOTIFY → COMPLETE

7. Reviewer UI (HTML)

A simple UI (ui/reviewer.html) for:

Entering checkpoint ID

Adding reviewer notes

Accept/Reject actions


FastAPI Endpoints
Method	Endpoint		Purpose
POST	/start-workflow		Start invoice workflow
GET	/human-review/pending	List pending HITL items
POST	/human-review/decision	Submit Accept/Reject
GET	/ui/reviewer.html	Reviewer UI

<<<<<<< HEAD
=======

>>>>>>> f253c5b (Updated main.py to handle HITL workflow and reviewer)
Installation:


git clone https://github.com/mkaamraan/Invoice-Lang-Graph
cd invoice-workflow
python -m venv venv

Activate the virtual environment:

Windows: venv\Scripts\activate
Linux/Mac: source venv/bin/activate

Install dependencies:

pip install -r requirements.txt


Usage:

1. Start the FastAPI server:
uvicorn main:app --reload

2. Test with sample invoice:
curl -X POST http://127.0.0.1:8000/start-workflow \
     -H "Content-Type: application/json" \
     -d @sample_invoice.json

3. Access Reviewer UI:
http://127.0.0.1:8000/ui/reviewer.html


Workflow currently flags high-risk vendors and missing tax IDs, but does not automatically pause for them.

Duplicate invoice detection is not implemented yet.

Fully offline simulation, no real ERP or OCR keys needed.