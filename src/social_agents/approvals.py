from __future__ import annotations
import json
import sqlite3
import uuid
from datetime import datetime

def utc_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

class ApprovalsStore:
    def __init__(self, db_path: str, schema_path: str):
        self.db_path = db_path
        self.schema_path = schema_path

    def init_db(self) -> None:
        with open(self.schema_path, "r", encoding="utf-8") as f:
            sql = f.read()
        con = sqlite3.connect(self.db_path)
        try:
            con.executescript(sql)
            con.commit()
        finally:
            con.close()

    def create_request(
        self,
        platform: str,
        account_id: str,
        action_type: str,
        draft_payload: dict,
        risk_level: str,
        risk_reason: str,
        confidence: float,
        expected_impact: dict,
        related_post_id: str | None,
        priority: int = 1,
        budget_amount: float | None = None,
    ) -> str:
        rid = str(uuid.uuid4())
        con = sqlite3.connect(self.db_path)
        try:
            con.execute(
                """
                INSERT INTO approval_requests
                (id, created_at, created_by, platform, account_id, action_type, status, priority,
                 risk_level, risk_reason, confidence, expected_impact, budget_amount, related_post_id, draft_payload)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    rid, utc_iso(), "agent:recommendation", platform, account_id, action_type, "PENDING", priority,
                    risk_level, risk_reason, float(confidence),
                    json.dumps(expected_impact),
                    budget_amount,
                    related_post_id,
                    json.dumps(draft_payload),
                )
            )
            con.commit()
        finally:
            con.close()
        return rid

    def list_pending(self) -> list[dict]:
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        try:
            rows = con.execute(
                "SELECT * FROM approval_requests WHERE status='PENDING' ORDER BY priority ASC, created_at DESC"
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            con.close()

    def approve(self, request_id: str) -> None:
        con = sqlite3.connect(self.db_path)
        try:
            con.execute("UPDATE approval_requests SET status='APPROVED' WHERE id=?", (request_id,))
            con.commit()
        finally:
            con.close()

    def reject(self, request_id: str) -> None:
        con = sqlite3.connect(self.db_path)
        try:
            con.execute("UPDATE approval_requests SET status='REJECTED' WHERE id=?", (request_id,))
            con.commit()
        finally:
            con.close()
