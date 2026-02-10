CREATE TABLE IF NOT EXISTS approval_requests (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  created_by TEXT NOT NULL,
  platform TEXT NOT NULL,
  account_id TEXT NOT NULL,
  action_type TEXT NOT NULL,
  status TEXT NOT NULL,
  priority INTEGER NOT NULL,
  risk_level TEXT NOT NULL,
  risk_reason TEXT,
  confidence REAL,
  expected_impact TEXT,
  budget_amount REAL,
  related_post_id TEXT,
  draft_payload TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS executions (
  id TEXT PRIMARY KEY,
  request_id TEXT NOT NULL,
  executed_at TEXT,
  executor TEXT NOT NULL,
  status TEXT NOT NULL,
  platform_response TEXT,
  error_message TEXT,
  FOREIGN KEY(request_id) REFERENCES approval_requests(id)
);
