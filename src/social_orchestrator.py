from __future__ import annotations
from pathlib import Path

from src.social_agents.ingestion import SocialIngestionAgent
from src.social_agents.quality import SocialDataQualityAgent
from src.social_agents.kpis import SocialKPIAgent
from src.social_agents.recommend import SocialRecommendationAgent
from src.social_agents.approvals import ApprovalsStore

def run_social_pipeline(dataset_path: str) -> dict:
    """
    Social pipeline returns a dict shaped similarly to your sales pipeline:
    - meta/dq
    - kpis (scalar)
    - monthly_df/top_posts_df breakdown tables
    - recommendations
    - pending approvals
    """
    ingestion = SocialIngestionAgent()
    quality = SocialDataQualityAgent()
    kpi_agent = SocialKPIAgent()
    reco_agent = SocialRecommendationAgent()

    df_raw, meta = ingestion.run(dataset_path)
    df_clean, dq = quality.run(df_raw)
    kpis = kpi_agent.run(df_clean)
    recs = reco_agent.run(df_clean, kpis)

    # approvals DB
    Path("db").mkdir(exist_ok=True)
    approvals_db = "db/approvals.db"
    schema_path = "schemas/approvals_sqlite.sql"
    store = ApprovalsStore(db_path=approvals_db, schema_path=schema_path)
    store.init_db()

    # create approval requests for risky ACTION recs
    for r in recs:
        if r.get("kind") == "ACTION" and r.get("risk_level") == "HIGH":
            store.create_request(
                platform="instagram",
                account_id=str(df_clean["account_id"].iloc[0]),
                action_type=r.get("action_type", "ACTION"),
                draft_payload=r.get("draft_payload", {}),
                risk_level=r.get("risk_level", "HIGH"),
                risk_reason=r.get("why", "Requires approval"),
                confidence=float(r.get("confidence", 0.7)),
                expected_impact=r.get("expected_impact", {}),
                related_post_id=r.get("draft_payload", {}).get("post_id"),
                priority=1,
                budget_amount=float(r.get("draft_payload", {}).get("amount", 0.0)) or None,
            )

    pending = store.list_pending()

    # split scalar KPIs vs tables (so Streamlit can render cleanly)
    scalar_kpis = {k: v for k, v in kpis.items() if not k.endswith("_df")}

    return {
        "meta": meta,
        "dq": dq,
        "kpis": scalar_kpis,
        "monthly_df": kpis["monthly_df"],
        "top_posts_df": kpis["top_posts_df"],
        "by_media_df": kpis["by_media_df"],
        "by_category_df": kpis["by_category_df"],
        "by_time_df": kpis["by_time_df"],
        "recommendations": recs,
        "pending_approvals": pending,
        "approvals_db": approvals_db,
    }
