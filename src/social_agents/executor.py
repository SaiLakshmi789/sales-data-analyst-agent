from __future__ import annotations
import json
import sqlite3
import uuid
from datetime import datetime

def utc_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

class DryRunExecutor:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def execute_approved(self) -> int:
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        count = 0
        try:
            rows = con.execute(
                "SELECT id, draft_payload FROM approval_requests WHERE status='APPROVED'"
            ).fetchall()

            for r in rows:
                exec_id = str(uuid.uuid4())
                payload = json.loads(r["draft_payload"])

                con.execute(
                    """
                    INSERT INTO executions (id, request_id, executed_at, executor, status, platform_response, error_message)
                    VALUES (?,?,?,?,?,?,?)
                    """,
                    (
                        exec_id, r["id"], utc_iso(), "agent:executor", "SUCCESS",
                        json.dumps({"dry_run": True, "payload": payload}),
                        None
                    )
                )
                con.execute("UPDATE approval_requests SET status='EXECUTED' WHERE id=?", (r["id"],))
                count += 1

            con.commit()
        finally:
            con.close()

        return count
