import os
from crewai import Agent, Task

from src.copilot.answerer import generate_executive_summary


def build_executive_agent() -> Agent:
    return Agent(
        role="Executive Insight Analyst",
        goal="Translate computed KPIs into an executive-ready business summary.",
        backstory=(
            "You are a senior data analyst who writes concise executive summaries "
            "based strictly on provided KPI values (no new calculations)."
        ),
        verbose=True,
        allow_delegation=False,
    )


def build_executive_summary_task(agent: Agent, kpis: dict) -> Task:
    use_gemini = os.getenv("USE_GEMINI", "false").lower() == "true"
    audience = os.getenv("SUMMARY_AUDIENCE", "executive")

    return Task(
        description=(
            "Generate an executive summary using the KPI values provided. "
            "If Gemini is enabled, use it only for narration; otherwise use the rule-based summary."
        ),
        expected_output="A concise executive summary in business language.",
        agent=agent,
        function=lambda: generate_executive_summary(
            kpis=kpis,
            use_gemini=use_gemini,
            audience=audience
        ),
    )
