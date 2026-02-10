from __future__ import annotations
import pandas as pd

class SocialDataQualityAgent:
    def run(self, df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
        dq: dict = {}

        before = len(df)
        df2 = df.drop_duplicates(subset=["post_id"]).copy()
        dq["dropped_duplicate_posts"] = int(before - len(df2))

        metric_cols = [
            "likes","comments","shares","saves","reach","impressions",
            "engagement_rate","followers_gained","engagements"
        ]
        for c in metric_cols:
            neg = int((df2[c] < 0).sum())
            if neg:
                df2.loc[df2[c] < 0, c] = 0
            dq[f"negative_fixed_{c}"] = neg

        dq["missing_pct"] = {c: float(df2[c].isna().mean()) for c in df2.columns}
        return df2, dq
