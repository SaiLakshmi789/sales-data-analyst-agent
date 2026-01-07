from __future__ import annotations

from src.config import PipelineConfig, ensure_dirs
from src.agents.ingestion import IngestionAgent
from src.agents.quality import DataQualityAgent
from src.agents.eda import EDAAgent
from src.agents.kpis import KPIAgent
from src.agents.viz import VizAgent
from src.agents.report import ReportAgent


def run_pipeline(dataset_path: str) -> dict:
    """
    Runs the full agent pipeline and RETURNS results + artifact paths.
    This keeps CLI usage working and enables Streamlit UI.
    """
    cfg = PipelineConfig()
    ensure_dirs(cfg)

    ingestion = IngestionAgent()
    quality = DataQualityAgent()
    eda_agent = EDAAgent()
    kpi_agent = KPIAgent()
    viz_agent = VizAgent()
    report_agent = ReportAgent()

    # 1) Ingest
    df_raw, meta = ingestion.run(dataset_path)

    # 2) Quality + cleaning
    df_clean, dq = quality.run(df_raw, cfg)

    # 3) EDA
    eda = eda_agent.run(df_clean)

    # 4) KPIs
    kpis = kpi_agent.run(df_clean)

    # 5) Save tables
    monthly_csv_path = cfg.tables_dir / "monthly_kpis.csv"
    product_csv_path = cfg.tables_dir / "product_kpis_top200.csv"
    report_agent.save_csv(kpis["monthly_df"], monthly_csv_path)
    report_agent.save_csv(kpis["product_df"].head(200), product_csv_path)

    # 6) Charts (your viz.py already returns file paths ✔)
    revenue_chart_path = viz_agent.plot_monthly_revenue(
        kpis["monthly_df"], cfg.charts_dir
    )
    orders_chart_path = viz_agent.plot_monthly_orders(
        kpis["monthly_df"], cfg.charts_dir
    )
    top_products_chart_path = viz_agent.plot_top_products(
        kpis["product_df"], cfg.charts_dir, n=10
    )

    # 7) Save reports
    ingestion_meta_path = cfg.output_dir / "ingestion_meta.json"
    dq_report_path = cfg.output_dir / "data_quality_report.json"
    eda_report_path = cfg.output_dir / "eda_report.json"
    kpi_summary_path = cfg.output_dir / "kpi_summary.json"
    exec_summary_path = cfg.output_dir / "executive_summary.md"

    report_agent.save_json(meta, ingestion_meta_path)
    report_agent.save_json(dq, dq_report_path)
    report_agent.save_json(eda, eda_report_path)

    kpi_summary = {k: v for k, v in kpis.items() if not k.endswith("_df")}
    report_agent.save_json(kpi_summary, kpi_summary_path)

    # 8) Executive summary (deterministic, no LLM)
    md = report_agent.executive_summary(kpis=kpis, dq=dq, eda=eda)
    report_agent.write_markdown(md, exec_summary_path)

    print("✅ Pipeline completed. Check the /outputs folder.")

    # 🔑 RETURN EVERYTHING STREAMLIT NEEDS
    return {
        "config": cfg,
        "meta": meta,
        "dq": dq,
        "eda": eda,
        "kpis": kpi_summary,
        "monthly_df": kpis["monthly_df"],
        "product_df": kpis["product_df"],
        "artifacts": {
            "ingestion_meta": str(ingestion_meta_path),
            "dq_report": str(dq_report_path),
            "eda_report": str(eda_report_path),
            "kpi_summary": str(kpi_summary_path),
            "exec_summary": str(exec_summary_path),
            "monthly_csv": str(monthly_csv_path),
            "product_csv": str(product_csv_path),
            "charts": {
                "monthly_revenue": revenue_chart_path,
                "monthly_orders": orders_chart_path,
                "top_products": top_products_chart_path,
            },
        },
    }
