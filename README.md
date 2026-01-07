# 🛒 Sales Data Analyst Agent

🚀 **Live Demo:** 
https://sales-data-analyst-agent.streamlit.app/*(You can explore this app even without local setup if you click on this link, make sure to upload the dataset from the link i mentioned in the end)*

An **agent-based, LLM-free sales analytics system** built using **Python, Pandas, and Streamlit** to automate data cleaning, KPI computation, visualization, and executive reporting.

---

## 🔍 Overview

This project demonstrates how an **agentic analytics architecture** can be applied to real-world sales data without relying on LLMs.  
Each stage of the analytics workflow is handled by an independent agent and orchestrated end-to-end.

---

## ✨ Features

- Modular agent architecture  
  *(Ingestion, Data Quality, EDA, KPI, Visualization, Reporting)*
- Supports **CSV and Excel (.xlsx / .xls)** datasets
- Computes key sales KPIs:
  - Revenue (Gross, Returns, Net)
  - Average Order Value (AOV)
  - Month-over-Month (MoM) growth
  - Top products
  - Customer metrics (repeat rate, revenue per customer)
- Interactive **Streamlit UI**
- Deterministic, reproducible, and **ATS-friendly**
- No API keys or LLM dependencies

---

## 🧠 Agentic Design

Each agent has a single responsibility and produces clear outputs:

- **IngestionAgent** – Load and validate raw data
- **DataQualityAgent** – Clean data and flag returns/cancellations
- **EDAAgent** – Generate descriptive insights
- **KPIAgent** – Compute business KPIs
- **VizAgent** – Create analytical charts
- **ReportAgent** – Generate executive summary
- **Orchestrator** – Coordinates the full pipeline

---

## ▶️ Run Locally

```bash
pip install -r requirements.txt
python -m streamlit run streamlit_app.py


Upload the Online Retail dataset (.csv or .xlsx) when prompted.

Dataset is not included in this repository.
Download from Kaggle:
https://www.kaggle.com/datasets/ulrikthygepedersen/online-retail-dataset

## 🔮 Next Steps

- Add optional LLM-powered insight agent for KPI explanations
- Enable natural-language querying over sales data
- Integrate external APIs while preserving deterministic core logic
