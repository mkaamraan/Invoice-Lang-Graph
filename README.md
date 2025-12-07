# AI-Powered Invoice Processing Workflow (with HITL Checkpointing)

This repository contains a complete AI-driven invoice processing workflow, built using a modular multi-stage architecture inspired by **LangGraph-style orchestration**. It demonstrates real-world workflow automation with Human-in-the-Loop (HITL) checkpoints for exceptional cases.

---

## Key Highlights

- **Modular Multi-Node Architecture**: Each stage (INTAKE → UNDERSTAND → PREPARE → RETRIEVE → MATCH → HITL → RECONCILE → APPROVE → POSTING → NOTIFY → COMPLETE) is a separate node, following LangGraph/Temporal workflow patterns.
- **AI-Assisted Invoice Understanding**: OCR simulation, vendor normalization, enrichment, line-item parsing, and risk scoring.
- **Two-Way PO Matching**: Compares invoice vs ERP PO, calculates match score, and pauses workflow automatically if threshold not met.
- **Human-In-The-Loop (HITL) Checkpoints**: Workflow pauses on failed matches; reviewers can Accept/Reject via a simple UI (`reviewer.html`), with automatic workflow resume on acceptance.
- **ERP Lookups (Simulated)**: Offline mock ERP integration for PO, GRN, and vendor history lookups.
- **Complete FastAPI Backend**: Endpoints for starting workflow, listing HITL items, submitting reviewer decisions, and accessing reviewer UI.

---

## Key Features

### 1. Modular Multi-Node Workflow
Each stage is implemented as a separate file under `nodes/`:

```
INTAKE → UNDERSTAND → PREPARE → RETRIEVE → MATCH
→ CHECKPOINT_HITL (Pause Workflow)
→ RECONCILE → APPROVE → POSTING → NOTIFY → COMPLETE
```

- Each node accepts the workflow state, performs a specific task, appends logs, and returns the updated state.
- Pattern inspired by production workflow engines: LangGraph, Temporal, Airflow, AWS Step Functions.

### 2. AI-Assisted Invoice Understanding
Simulated workflow includes:

- OCR extraction (Tesseract or AWS Textract)
- Vendor normalization
- Vendor metadata enrichment
- Line-item parsing
- Risk flag generation
- Smart tool selection (BigTool picker)

### 3. ERP Lookups (Simulated)
Data retrieval includes:

- Purchase Order (PO) lookup
- Goods Received Note (GRN) lookup
- Vendor payment history

**Fully offline simulation**, no real ERP keys required.

### 4. Two-Way PO Matching
Workflow computes:

- Amount difference
- Line-item similarity
- Risk scoring
- Final match score (0–1)

If `score < threshold`, workflow is **PAUSED** → HITL required.

### 5. Human-In-The-Loop (HITL) Checkpointing
- Workflow state is saved into SQLite.
- A checkpoint ID is created.
- Reviewer UI allows **Accept/Reject** with notes.
- ACCEPT → workflow resumes automatically.
- REJECT → workflow ends as `MANUAL_HANDOFF`.

Dynamic HITL reasons are calculated per invoice:

- Amount mismatch
- Vendor mismatch
- Line-item mismatch
- OCR parsing errors
- ERP matching issues

### 6. Workflow Auto-Resume After Approval
After HITL acceptance:

```
RECONCILE → APPROVE → POSTING → NOTIFY → COMPLETE
```

### 7. Reviewer UI (HTML)
Simple UI located at `ui/reviewer.html`:

- Enter checkpoint ID
- Review invoice details
- Accept/Reject actions with optional notes
- Displays only the **specific HITL reason** for review

---

## FastAPI Endpoints

| Method | Endpoint                     | Purpose                           |
|--------|-------------------------------|-----------------------------------|
| POST   | /start-workflow              | Start invoice workflow            |
| GET    | /human-review/pending        | List pending HITL items           |
| POST   | /human-review/decision       | Submit Accept/Reject decision     |
| GET    | /ui/reviewer.html            | Reviewer UI                       |

---

## Installation

```bash
git clone https://github.com/mkaamraan/Invoice-Lang-Graph
cd Invoice-Lang-Graph
python -m venv venv
```

Activate virtual environment:

- **Windows**: `venv\Scripts\activate`  
- **Linux/Mac**: `source venv/bin/activate`

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Usage

1. **Start the FastAPI server:**
```bash
uvicorn main:app --reload
```

2. **Submit a sample invoice:**
```bash
curl -X POST http://127.0.0.1:8000/start-workflow \
     -H "Content-Type: application/json" \
     -d @sample_invoices/sample_invoice1.json
```

3. **Access Reviewer UI:**
```
http://127.0.0.1:8000/ui/reviewer.html?checkpoint_id=<checkpoint_id>
```

---

## Notes

- HITL is triggered **only for invoices that require human attention**.
- High-risk vendors or missing tax IDs can be flagged (configurable) but do not automatically pause workflow.
- Duplicate invoice detection is not implemented yet.

---

## License

MIT License

