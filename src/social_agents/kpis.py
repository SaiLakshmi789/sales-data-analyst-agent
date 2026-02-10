from __future__ import annotations
import pandas as pd

class SocialKPIAgent:
    def run(self, df: pd.DataFrame) -> dict:
        total_posts = int(df["post_id"].nunique())
        total_impressions = float(df["impressions"].sum())
        total_reach = float(df["reach"].sum())
        total_engagements = float(df["engagements"].sum())
        total_followers_gained = float(df["followers_gained"].sum())

        avg_engagements_per_post = float(total_engagements / total_posts) if total_posts else 0.0
        avg_engagement_rate = float(df["engagement_rate"].mean()) if len(df) else 0.0

        denom = total_impressions if total_impressions else (total_reach if total_reach else 0.0)
        weighted_er = float(total_engagements / denom) if denom else 0.0

        # Monthly trend
        tmp = df.copy()
        tmp["month"] = tmp["created_at"].dt.to_period("M").astype(str)
        monthly = (
            tmp.groupby("month")
               .agg(
                   posts=("post_id","nunique"),
                   impressions=("impressions","sum"),
                   reach=("reach","sum"),
                   engagements=("engagements","sum"),
                   followers_gained=("followers_gained","sum"),
                   avg_er=("engagement_rate","mean"),
               )
               .reset_index()
               .sort_values("month")
        )
        monthly["mom_engagements_growth_pct"] = monthly["engagements"].pct_change() * 100
        monthly["mom_impressions_growth_pct"] = monthly["impressions"].pct_change() * 100

        # Top posts
        top_posts = (
            tmp.sort_values(["engagements","engagement_rate"], ascending=False)
               .loc[:, [
                   "post_id","account_id","created_at","media_type","content_category",
                   "traffic_source","has_call_to_action",
                   "impressions","reach","likes","comments","shares","saves","engagements",
                   "engagement_rate","followers_gained","hashtags_count","caption_length",
                   "performance_bucket_label"
               ]]
               .head(50)
        )

        # Breakdowns for strategy
        by_media = (
            tmp.groupby("media_type")
               .agg(posts=("post_id","nunique"),
                    avg_er=("engagement_rate","mean"),
                    engagements=("engagements","sum"),
                    followers_gained=("followers_gained","sum"))
               .reset_index()
               .sort_values("avg_er", ascending=False)
        )

        by_category = (
            tmp.groupby("content_category")
               .agg(posts=("post_id","nunique"),
                    avg_er=("engagement_rate","mean"),
                    engagements=("engagements","sum"),
                    followers_gained=("followers_gained","sum"))
               .reset_index()
               .sort_values("avg_er", ascending=False)
        )

        by_time = (
            tmp.groupby(["day_of_week","post_hour"])
               .agg(posts=("post_id","nunique"),
                    median_er=("engagement_rate","median"),
                    avg_er=("engagement_rate","mean"))
               .reset_index()
               .sort_values(["median_er","posts"], ascending=False)
        )

        return {
            "total_posts": total_posts,
            "total_impressions": total_impressions,
            "total_reach": total_reach,
            "total_engagements": total_engagements,
            "total_followers_gained": total_followers_gained,
            "avg_engagements_per_post": avg_engagements_per_post,
            "avg_engagement_rate": avg_engagement_rate,
            "weighted_engagement_rate": weighted_er,
            "monthly_df": monthly,
            "top_posts_df": top_posts,
            "by_media_df": by_media,
            "by_category_df": by_category,
            "by_time_df": by_time,
        }
