import sqlite3
import json
import uuid
from datetime import datetime
from typing import Optional

DB_PATH = "./demo.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS checkpoints (
        id TEXT PRIMARY KEY,
        invoice_id TEXT,
        state_blob TEXT,
        status TEXT,
        created_at TEXT,
        resume_token TEXT
    )
    """)
    conn.commit()
    conn.close()

def save_checkpoint(invoice_id: str, state: dict, status: str = "PAUSED") -> str:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cid = str(uuid.uuid4())
    resume_token = str(uuid.uuid4())
    cur.execute(
        "INSERT INTO checkpoints (id, invoice_id, state_blob, status, created_at, resume_token) VALUES (?,?,?,?,?,?)",
        (cid, invoice_id, json.dumps(state), status, datetime.utcnow().isoformat(), resume_token)
    )
    conn.commit()
    conn.close()
    return cid

def get_pending_checkpoints():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, invoice_id, state_blob, status, created_at, resume_token FROM checkpoints WHERE status = 'PAUSED'")
    rows = cur.fetchall()
    conn.close()
    result = []
    for r in rows:
        result.append({
            "checkpoint_id": r[0],
            "invoice_id": r[1],
            "state": json.loads(r[2]),
            "status": r[3],
            "created_at": r[4],
            "resume_token": r[5]
        })
    return result

def get_checkpoint(checkpoint_id: str) -> Optional[dict]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, invoice_id, state_blob, status, created_at, resume_token FROM checkpoints WHERE id=?", (checkpoint_id,))
    r = cur.fetchone()
    conn.close()
    if not r:
        return None
    return {
        "checkpoint_id": r[0],
        "invoice_id": r[1],
        "state": json.loads(r[2]),
        "status": r[3],
        "created_at": r[4],
        "resume_token": r[5]
    }

def update_checkpoint_status(checkpoint_id: str, status: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE checkpoints SET status=? WHERE id=?", (status, checkpoint_id))
    conn.commit()
    conn.close()
