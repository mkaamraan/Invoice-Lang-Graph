import sqlite3
import json
from datetime import datetime

DB_FILE = "checkpoints.db"


def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS checkpoints (
        checkpoint_id TEXT PRIMARY KEY,
        created_at TEXT,
        state TEXT,
        status TEXT,
        resume_token TEXT
    )
    ''')
    conn.commit()
    conn.close()


def save_checkpoint(checkpoint_id, state, status="PAUSED", resume_token=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
    INSERT OR REPLACE INTO checkpoints (checkpoint_id, created_at, state, status, resume_token)
    VALUES (?, ?, ?, ?, ?)
    ''', (checkpoint_id, datetime.now().isoformat(), json.dumps(state), status, resume_token))
    conn.commit()
    conn.close()


def get_checkpoint(checkpoint_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT state, status, resume_token FROM checkpoints WHERE checkpoint_id=?", (checkpoint_id,))
    row = c.fetchone()
    conn.close()

    if row:
        return {
            "state": json.loads(row[0]),
            "status": row[1],
            "resume_token": row[2]
        }
    return None


def get_pending_checkpoints():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT checkpoint_id, created_at, state FROM checkpoints WHERE status='PAUSED'")
    rows = c.fetchall()
    conn.close()

    res = []
    for r in rows:
        res.append({
            "checkpoint_id": r[0],
            "created_at": r[1],
            "state": json.loads(r[2])
        })
    return res


# ✅ ADDING THIS FUNCTION — REQUIRED BY main.py
def update_checkpoint(checkpoint_id, updates: dict):
    """
    Update any fields inside the checkpoint row.
    Example usage:
        update_checkpoint("abc123", {"status": "RESOLVED"})
    """

    # Fetch existing record
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT state, status, resume_token FROM checkpoints WHERE checkpoint_id=?", (checkpoint_id,))
    row = c.fetchone()

    if not row:
        conn.close()
        return False

    # Unpack existing values
    state_json, status, resume_token = row
    state_dict = json.loads(state_json)

    # Apply updates
    if "state" in updates:
        state_dict.update(updates["state"])

    new_status = updates.get("status", status)
    new_resume_token = updates.get("resume_token", resume_token)

    # Update DB row
    c.execute('''
        UPDATE checkpoints
        SET state=?, status=?, resume_token=?
        WHERE checkpoint_id=?
    ''', (json.dumps(state_dict), new_status, new_resume_token, checkpoint_id))

    conn.commit()
    conn.close()
    return True
