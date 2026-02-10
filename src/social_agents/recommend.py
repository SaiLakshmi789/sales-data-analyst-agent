from __future__ import annotations
import numpy as np
import pandas as pd

class SocialRecommendationAgent:
    def run(self, df: pd.DataFrame, kpis: dict) -> list[dict]:
        recs: list[dict] = []

        # Best posting time slots
        time_tbl = (
            df.groupby(["day_of_week","post_hour"])
              .agg(posts=("post_id","nunique"), median_er=("engagement_rate","median"))
              .reset_index()
              .query("posts >= 3")
              .sort_values("median_er", ascending=False)
        )
        top_times = time_tbl.head(3).to_dict(orient="records")
        if top_times:
            recs.append({
                "kind": "STRATEGY",
                "title": "Post at higher-performing times",
                "why": "These day/hour slots show the best median engagement rate in your dataset.",
                "risk_level": "LOW",
                "confidence": 0.8,
                "evidence": {"top_times": top_times},
                "expected_impact": {"metric": "engagement_rate", "delta_pct": 5.0, "horizon_days": 14},
            })

        # CTA effectiveness
        cta_tbl = df.groupby("has_call_to_action")["engagement_rate"].mean()
        if True in cta_tbl.index and False in cta_tbl.index:
            delta = (float(cta_tbl[True]) - float(cta_tbl[False])) / max(1e-9, abs(float(cta_tbl[False]))) * 100.0
            recs.append({
                "kind": "CONTENT",
                "title": "Use CTA more consistently",
                "why": f"CTA posts show Δ {delta:.1f}% average engagement rate vs non-CTA posts.",
                "risk_level": "LOW",
                "confidence": 0.75,
                "evidence": {"cta_avg_er_true": float(cta_tbl[True]), "cta_avg_er_false": float(cta_tbl[False]), "delta_pct": delta},
                "expected_impact": {"metric": "engagement_rate", "delta_pct": float(max(delta, 0.0)), "horizon_days": 30},
            })

        # Boost candidate (approval-needed action)
        er = df["engagement_rate"].to_numpy()
        thresh = float(np.quantile(er, 0.95)) if len(er) else 0.0
        imp_med = float(df["impressions"].median()) if len(df) else 0.0
        cand = df[(df["engagement_rate"] >= thresh) & (df["impressions"] >= imp_med)].copy()
        cand = cand.sort_values(["engagement_rate","impressions"], ascending=False).head(3)

        for _, row in cand.iterrows():
            recs.append({
                "kind": "ACTION",
                "title": f"Boost post {row['post_id']}",
                "why": "High engagement rate + strong impressions → good boost candidate.",
                "risk_level": "HIGH",
                "confidence": 0.8,
                "evidence": {
                    "post_id": row["post_id"],
                    "engagement_rate": float(row["engagement_rate"]),
                    "impressions": float(row["impressions"]),
                    "media_type": row["media_type"],
                    "content_category": row["content_category"],
                },
                "expected_impact": {"metric": "impressions", "delta_pct": 15.0, "horizon_days": 7},
                "action_type": "BOOST_POST",
                "draft_payload": {
                    "post_id": row["post_id"],
                    "amount": 50,
                    "days": 3,
                    "objective": "PROFILE_VISITS"
                }
            })

        return recs
