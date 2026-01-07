import json
from pathlib import Path

class ReportAgent:
    def save_json(self, obj: dict, path: Path) -> str:
        path.write_text(json.dumps(obj, indent=2, default=str), encoding="utf-8")
        return str(path)

    def save_csv(self, df, path: Path) -> str:
        df.to_csv(path, index=False)
        return str(path)

    def executive_summary(self, kpis: dict, dq: dict, eda: dict) -> str:
        # Deterministic, business-friendly summary (no LLM)
        lines = []
        lines.append("# Executive Summary — Online Retail Sales\n")

        lines.append(
            f"- **Net Revenue:** {kpis['net_revenue']:.2f} "
            f"(Gross: {kpis['gross_revenue']:.2f}, Returns: {kpis['return_revenue']:.2f})"
        )
        lines.append(
            f"- **Orders:** {kpis['orders']} | **AOV:** {kpis['aov']:.2f} | **Units Sold:** {kpis['units_sold']:.0f}"
        )
        lines.append(
            f"- **Customers:** {kpis['active_customers']} | "
            f"**Repeat Rate:** {kpis['repeat_customer_rate']*100:.1f}% | "
            f"**Revenue/Customer:** {kpis['revenue_per_customer']:.2f}"
        )
        lines.append(f"- **Time Range:** {eda.get('date_min')} → {eda.get('date_max')}")
        lines.append(
            f"- **Data Quality:** {dq.get('rows_initial')} rows ingested; "
            f"{dq.get('rows_after_clean')} rows after cleaning; "
            f"{dq.get('return_rows')} return/cancellation rows flagged."
        )

        lines.append("\n## Recommended Next Actions")
        lines.append("- Investigate high-return products and extreme quantity/price outliers for potential operational or data issues.")
        lines.append("- Add customer segmentation (RFM/cohorts) to identify high-value repeat customers and retention opportunities.")
        lines.append("- Track country-level revenue concentration to assess dependency risk.\n")

        return "\n".join(lines)

    def write_markdown(self, text: str, path: Path) -> str:
        path.write_text(text, encoding="utf-8")
        return str(path)
