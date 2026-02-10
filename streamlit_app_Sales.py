import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from src.orchestrator import run_pipeline


def make_arrow_compatible(df: pd.DataFrame) -> pd.DataFrame:
    """
    Streamlit uses Arrow to render dataframes. Arrow fails on object columns with mixed
    types (e.g., StockCode having both ints and strings).
    Convert object columns to string to avoid ArrowTypeError.
    """
    df = df.copy()
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].astype(str)
    return df


st.set_page_config(page_title="Sales Data Analyst Agent", layout="wide")

st.title("🛒 Sales Data Analyst Agent")
st.caption(
    "Upload the Online Retail dataset, run the agent pipeline, and get KPIs, charts, and an executive summary."
)

# Sidebar controls
st.sidebar.header("Run Settings")
show_top_n = st.sidebar.slider("Show top products (table)", min_value=10, max_value=200, value=50, step=10)

uploaded = st.file_uploader("Upload the Online Retail dataset", type=["csv", "xlsx", "xls"])

if uploaded is None:
    st.info("Upload a dataset to begin.")
    st.stop()

# Save uploaded file to a temp path (so pandas can read it)
with tempfile.TemporaryDirectory() as tmpdir:
    tmp_path = Path(tmpdir) / uploaded.name
    tmp_path.write_bytes(uploaded.getbuffer())

    st.success(f"Uploaded: {uploaded.name}")

    with st.expander("Preview raw data"):
        path = Path(tmp_path)
        suffix = path.suffix.lower()

        if suffix == ".csv":
            raw_preview = pd.read_csv(path, encoding="ISO-8859-1")
        elif suffix in [".xlsx", ".xls"]:
            raw_preview = pd.read_excel(path)
        else:
            st.error(f"Unsupported file type: {suffix}")
            st.stop()

        st.dataframe(make_arrow_compatible(raw_preview.head(20)), width="stretch")

    if st.button("🚀 Run Agent Pipeline", type="primary"):
        with st.spinner("Running agents: ingestion → quality → eda → kpis → viz → report ..."):
            results = run_pipeline(dataset_path=str(tmp_path))

        st.success("Pipeline completed! Outputs are saved under /outputs and also shown below.")

        # --- KPI Cards ---
        k = results["kpis"]
        dq = results["dq"]
        eda = results["eda"]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Net Revenue", f"{k['net_revenue']:.2f}")
        c2.metric("Orders", f"{k['orders']}")
        c3.metric("AOV", f"{k['aov']:.2f}")
        c4.metric("Repeat Rate", f"{k['repeat_customer_rate'] * 100:.1f}%")

        c5, c6, c7, c8 = st.columns(4)
        c5.metric("Gross Revenue", f"{k['gross_revenue']:.2f}")
        c6.metric("Return Revenue", f"{k['return_revenue']:.2f}")
        c7.metric("Active Customers", f"{k['active_customers']}")
        c8.metric("Revenue / Customer", f"{k['revenue_per_customer']:.2f}")

        # --- Data Quality & EDA ---
        with st.expander("🧪 Data Quality Report"):
            st.json(dq)

        with st.expander("🔎 EDA Summary"):
            st.json(eda)

        # --- Tables ---
        st.subheader("📈 Monthly KPIs")
        st.dataframe(make_arrow_compatible(results["monthly_df"]), width="stretch")

        st.subheader("🏷️ Top Products")
        st.dataframe(make_arrow_compatible(results["product_df"].head(show_top_n)), width="stretch")

        # --- Charts (from saved PNGs) ---
        st.subheader("📊 Charts")
        charts = results["artifacts"]["charts"]
        chart_cols = st.columns(3)

        for idx, (name, chart_path) in enumerate(charts.items()):
            p = Path(chart_path)
            if p.exists():
                with chart_cols[idx % 3]:
                    st.image(str(p), caption=name.replace("_", " ").title(), use_container_width=True)
            else:
                with chart_cols[idx % 3]:
                    st.warning(f"Missing chart: {name}")

        # --- Executive Summary ---
        st.subheader("📝 Executive Summary")
        exec_path = Path(results["artifacts"]["exec_summary"])
        if exec_path.exists():
            md_text = exec_path.read_text(encoding="utf-8")
            st.markdown(md_text)

            st.download_button(
                "⬇️ Download Executive Summary (MD)",
                data=md_text,
                file_name="executive_summary.md",
                mime="text/markdown",
            )
        else:
            st.error("Executive summary file not found.")

        # --- Download key artifacts ---
        st.subheader("📦 Download Output Files")
        artifact_files = {
            "KPI Summary (JSON)": results["artifacts"]["kpi_summary"],
            "Data Quality Report (JSON)": results["artifacts"]["dq_report"],
            "EDA Report (JSON)": results["artifacts"]["eda_report"],
            "Monthly KPIs (CSV)": results["artifacts"]["monthly_csv"],
            "Top Products (CSV)": results["artifacts"]["product_csv"],
        }

        for label, fpath in artifact_files.items():
            p = Path(fpath)
            if p.exists():
                st.download_button(
                    f"⬇️ {label}",
                    data=p.read_bytes(),
                    file_name=p.name,
                )
