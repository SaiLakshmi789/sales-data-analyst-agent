from __future__ import annotations
import pandas as pd

REQUIRED_COLS = [
    "post_id","account_id","account_type","follower_count","media_type","content_category",
    "traffic_source","has_call_to_action","post_datetime","post_date","post_hour","day_of_week",
    "likes","comments","shares","saves","reach","impressions","engagement_rate","followers_gained",
    "caption_length","hashtags_count","performance_bucket_label"
]

class SocialIngestionAgent:
    def run(self, csv_path: str) -> tuple[pd.DataFrame, dict]:
        df = pd.read_csv(csv_path)
        missing = [c for c in REQUIRED_COLS if c not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        out = df.copy()

        # Parse datetime (your format: 2024-11-30 6:00:00)
        out["created_at"] = pd.to_datetime(
            out["post_datetime"],
            format="%Y-%m-%d %H:%M:%S",
            errors="coerce"
        )
        out = out.dropna(subset=["created_at"])

        # Ensure consistent derived time fields (even if CSV has them)
        out["post_hour"] = out["created_at"].dt.hour
        out["day_of_week"] = out["created_at"].dt.day_name()

        # Numeric coercion
        num_cols = [
            "follower_count","likes","comments","shares","saves",
            "reach","impressions","engagement_rate","followers_gained",
            "caption_length","hashtags_count"
        ]
        for c in num_cols:
            out[c] = pd.to_numeric(out[c], errors="coerce").fillna(0)

        # Boolean CTA
        if out["has_call_to_action"].dtype != bool:
            out["has_call_to_action"] = out["has_call_to_action"].astype(str).str.lower().isin(
                ["1","true","yes","y"]
            )

        # Derived engagement
        out["engagements"] = out["likes"] + out["comments"] + out["shares"] + out["saves"]
        out["platform"] = "instagram"

        meta = {
            "rows": int(len(out)),
            "accounts": int(out["account_id"].nunique()),
            "date_min": str(out["created_at"].min()),
            "date_max": str(out["created_at"].max()),
        }
        return out, meta
