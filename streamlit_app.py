import streamlit as st
import pandas as pd
import os

# Your existing sales pipeline
from src.orchestrator import run_pipeline

# New social pipeline
from src.social_orchestrator import run_social_pipeline
from src.social_agents.approvals import ApprovalsStore
from src.social_agents.executor import DryRunExecutor

def make_arrow_compatible(df: pd.DataFrame) -> pd.DataFrame:
    # Streamlit Arrow compatibility helper
    out = df.copy()
    for c in out.columns:
        if pd.api.types.is_period_dtype(out[c]):
            out[c] = out[c].astype(str)
    return out

st.set_page_config(page_title="Agentic Analytics Copilot", layout="wide")

st.title("📊 Agentic Analytics Copilot")
st.caption("Sales Analytics Agent + Instagram Agentic Analyst (with approvals + dry-run executor)")

mode = st.sidebar.radio("Mode", ["Sales (Retail)", "Instagram Analytics"])

uploaded_file = st.sidebar.file_uploader("Upload dataset", type=["csv", "xlsx"])

show_top_n = st.sidebar.slider("Top N rows to display", 10, 200, 50)

if uploaded_file is None:
    st.info("Upload a dataset from the sidebar to begin.")
    st.stop()

# Save uploaded file locally
os.makedirs("data", exist_ok=True)
tmp_path = os.path.join("data", uploaded_file.name)
with open(tmp_path, "wb") as f:
    f.write(uploaded_file.getbuffer())

if st.sidebar.button("Run Pipeline"):
    if mode == "Sales (Retail)":
        results = run_pipeline(dataset_path=str(tmp_path))
    else:
        results = run_social_pipeline(dataset_path=str(tmp_path))
    st.session_state["results"] = results

results = st.session_state.get("results")
if not results:
    st.stop()

tab1, tab2, tab3 = st.tabs(["Dashboard", "Recommendations", "Approval Queue"])

with tab1:
    st.subheader("Dashboard")

    if mode == "Sales (Retail)":
        st.write("Sales KPIs")
        st.json(results.get("kpis", {}))

        if "monthly_df" in results:
            st.subheader("Monthly KPIs")
            st.dataframe(make_arrow_compatible(results["monthly_df"]), use_container_width=True)

        if "product_df" in results:
            st.subheader("Top Products")
            st.dataframe(make_arrow_compatible(results["product_df"].head(show_top_n)), use_container_width=True)

    else:
        k = results["kpis"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Posts", f"{k['total_posts']}")
        c2.metric("Total Engagements", f"{int(k['total_engagements'])}")
        c3.metric("Weighted ER", f"{k['weighted_engagement_rate']:.4f}")
        c4.metric("Followers Gained", f"{int(k['total_followers_gained'])}")

        c5, c6, c7, c8 = st.columns(4)
        c5.metric("Impressions", f"{int(k['total_impressions'])}")
        c6.metric("Reach", f"{int(k['total_reach'])}")
        c7.metric("Avg Eng/Post", f"{k['avg_engagements_per_post']:.2f}")
        c8.metric("Avg ER", f"{k['avg_engagement_rate']:.4f}")

        st.subheader("Monthly Trend")
        st.dataframe(make_arrow_compatible(results["monthly_df"]), use_container_width=True)

        st.subheader("Top Posts")
        st.dataframe(make_arrow_compatible(results["top_posts_df"].head(show_top_n)), use_container_width=True)

        st.subheader("Breakdowns")
        colA, colB = st.columns(2)
        with colA:
            st.write("By Media Type")
            st.dataframe(make_arrow_compatible(results["by_media_df"]), use_container_width=True)
        with colB:
            st.write("By Content Category")
            st.dataframe(make_arrow_compatible(results["by_category_df"]), use_container_width=True)

with tab2:
    st.subheader("Recommendations")
    recs = results.get("recommendations", [])
    if not recs:
        st.info("No recommendations generated.")
    else:
        for r in recs:
            with st.container(border=True):
                st.markdown(f"**{r.get('title','(no title)')}**")
                st.write(r.get("why",""))
                st.caption(f"Kind: {r.get('kind')} | Risk: {r.get('risk_level')} | Confidence: {r.get('confidence')}")
                if r.get("expected_impact"):
                    st.json(r["expected_impact"])
                if r.get("evidence"):
                    st.json(r["evidence"])

with tab3:
    st.subheader("Approval Queue (Human-in-the-loop)")

    if mode != "Instagram Analytics":
        st.info("Approval queue is enabled for Instagram mode in this implementation.")
        st.stop()

    approvals_db = results.get("approvals_db", "db/approvals.db")
    store = ApprovalsStore(db_path=approvals_db, schema_path="schemas/approvals_sqlite.sql")
    store.init_db()

    pending = store.list_pending()
    if not pending:
        st.info("No pending approvals.")
    else:
        for req in pending:
            with st.container(border=True):
                st.markdown(f"**{req['action_type']}** • `{req['id']}`")
                st.write(f"Risk: {req['risk_level']} — {req.get('risk_reason','')}")
                st.caption(f"Account: {req['account_id']} | Priority: {req['priority']}")

                st.write("Draft payload:")
                st.json(req["draft_payload"])

                col1, col2 = st.columns(2)
                if col1.button("Approve", key=f"approve_{req['id']}"):
                    store.approve(req["id"])
                    st.success("Approved.")
                    st.rerun()

                if col2.button("Reject", key=f"reject_{req['id']}"):
                    store.reject(req["id"])
                    st.warning("Rejected.")
                    st.rerun()

    st.divider()
    if st.button("Execute Approved (Dry-run)"):
        executor = DryRunExecutor(db_path=approvals_db)
        n = executor.execute_approved()
        st.success(f"Executed {n} approved actions (dry-run).")
        st.rerun()
