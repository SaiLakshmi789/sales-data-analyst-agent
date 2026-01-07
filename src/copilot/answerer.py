from __future__ import annotations

import json
import re
from typing import Dict, Any, Optional

from .router import Route, RoutedQuestion
from .retriever import ContextRetriever
from .prompts import build_insight_prompt


def _format_metrics(kpis: Dict[str, Any]) -> str:
    # Pretty JSON block to feed LLM safely
    return json.dumps(kpis, indent=2)


def _format_context(chunks) -> str:
    """
    Kept for INSIGHT mode (useful evidence block).
    For DEFINITION mode, we now use _format_definition_answer() instead.
    """
    if not chunks:
        return "No relevant context found."
    parts = []
    for c in chunks:
        parts.append(f"- (source: {c.source}, score: {c.score:.3f}) {c.text}")
    return "\n".join(parts)


def _metric_lookup(kpis: Dict[str, Any], question: str) -> str:
    """
    Robust, safe KPI lookup:
    - Normalizes the question (case/punct)
    - Matches against a list of aliases (synonyms)
    - Returns ONLY values that exist in kpi_summary.json
    - If unsure, asks user to choose from available KPIs (no hallucination)
    """
    q = question.lower()
    q = re.sub(r"[^a-z0-9\s]", " ", q)   # remove punctuation
    q = " ".join(q.split())

    # Aliases -> your JSON key
    aliases = {
        "gross_revenue": [
            "gross revenue", "gross sales", "total sales", "total revenue before returns", "sales before returns"
        ],
        "return_revenue": [
            "return revenue", "returns revenue", "returns", "refunds", "cancellations", "cancelled revenue"
        ],
        "net_revenue": [
            "net revenue", "net sales", "revenue after returns", "sales after returns", "net sales after returns"
        ],
        "orders": [
            "orders", "number of orders", "total orders", "order count", "invoices", "invoice count"
        ],
        "units_sold": [
            "units sold", "units", "quantity sold", "total units", "items sold"
        ],
        "aov": [
            "aov", "average order value", "avg order value", "average basket value", "basket value"
        ],
        "asp": [
            "asp", "average selling price", "avg selling price", "average price", "avg price per unit"
        ],
        "active_customers": [
            "active customers", "customers", "number of customers", "unique customers", "customer count"
        ],
        "repeat_customer_rate": [
            "repeat customer rate", "repeat rate", "returning customer rate", "repeat purchase rate", "repeat customers percent"
        ],
        "revenue_per_customer": [
            "revenue per customer", "sales per customer", "avg revenue per customer", "average revenue per customer"
        ],
    }

    # Helper: find best match using longest alias contained in question
    best_key = None
    best_alias_len = 0

    for key, alias_list in aliases.items():
        for a in alias_list:
            a_norm = re.sub(r"[^a-z0-9\s]", " ", a.lower())
            a_norm = " ".join(a_norm.split())
            if a_norm and a_norm in q:
                if len(a_norm) > best_alias_len:
                    best_key = key
                    best_alias_len = len(a_norm)

    # If we matched a KPI key, return only if it exists in kpis
    if best_key:
        if best_key in kpis:
            pretty = best_key.replace("_", " ").title()
            return f"{pretty}: {kpis[best_key]}"
        return f"I recognized the metric, but `{best_key}` is missing in outputs/kpi_summary.json."

    # Secondary: user asked for "revenue" but not clear which type
    if "revenue" in q or "sales" in q:
        options = ["gross_revenue", "net_revenue", "return_revenue"]
        available = [k for k in options if k in kpis]
        return (
            "Do you mean gross revenue, net revenue, or return revenue?\n"
            f"Available: {', '.join(available) if available else 'none found'}"
        )

    # Fallback: show what we CAN answer
    available = ", ".join(sorted(kpis.keys()))
    return (
        "I can answer metrics for: "
        f"{available}.\n"
        "Try: 'What is net revenue?', 'How many orders?', or 'What is average order value (AOV)?'"
    )



# -------------------------
# NEW: Clean definition formatting
# -------------------------

def _detect_kpi_key(question: str) -> Optional[str]:
    """
    Detect which KPI the definition question is about.
    Returns your kpi_summary.json key where possible.
    """
    q = question.lower()

    kpi_map = {
        "gross revenue": "gross_revenue",
        "return revenue": "return_revenue",
        "returns": "return_revenue",
        "net revenue": "net_revenue",
        "orders": "orders",
        "units sold": "units_sold",
        "aov": "aov",
        "average order value": "aov",
        "asp": "asp",
        "average selling price": "asp",
        "active customers": "active_customers",
        "repeat customer rate": "repeat_customer_rate",
        "repeat rate": "repeat_customer_rate",
        "revenue per customer": "revenue_per_customer",
    }

    for phrase in sorted(kpi_map.keys(), key=len, reverse=True):
        if phrase in q:
            return kpi_map[phrase]
    return None


def _kpi_heading_name(kpi_key: str) -> str:
    """
    Convert KPI key -> expected markdown heading title in kpi_definitions.md
    """
    mapping = {
        "gross_revenue": "Gross Revenue",
        "return_revenue": "Return Revenue",
        "net_revenue": "Net Revenue",
        "orders": "Orders",
        "units_sold": "Units Sold",
        "aov": "AOV (Average Order Value)",
        "asp": "ASP (Average Selling Price)",
        "active_customers": "Active Customers",
        "repeat_customer_rate": "Repeat Customer Rate",
        "revenue_per_customer": "Revenue per Customer",
    }
    return mapping.get(kpi_key, kpi_key)


def _extract_markdown_section(md_text: str, heading: str) -> Optional[str]:
    """
    Extract the section under:
      ## <heading>
    until the next "## ..." heading or end-of-text.
    """
    h = re.escape(heading.strip())
    pattern = rf"(?im)^\s*##\s*{h}\s*$([\s\S]*?)(?=^\s*##\s+|\Z)"
    m = re.search(pattern, md_text)
    if not m:
        return None
    section = m.group(1).strip()
    return section if section else None


def _format_definition_answer(question: str, retrieved_chunks) -> str:
    # detect KPI from question
    kpi_key = _detect_kpi_key(question)
    if kpi_key:
        wanted_heading = _kpi_heading_name(kpi_key)
        wanted_norm = _norm(wanted_heading)

        md = _read_context_file("kpi_definitions.md")
        sections = _parse_md_sections(md)

        # Try exact match
        if wanted_norm in sections:
            body = sections[wanted_norm]
            lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
            short = "\n".join(lines[:8])  # keep concise
            return f"{wanted_heading}:\n{short}\n\n(source: kpi_definitions.md)"

        # Try fuzzy contains match (handles headings like "net revenue (after returns)")
        for h_norm, body in sections.items():
            if wanted_norm in h_norm or h_norm in wanted_norm:
                lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
                short = "\n".join(lines[:8])
                return f"{wanted_heading}:\n{short}\n\n(source: kpi_definitions.md)"

    # fallback: trimmed snippet view from retrieval (still useful)
    if not retrieved_chunks:
        return "I couldn't find a relevant definition in the context files."

    snippets = []
    used_sources = []
    for ch in retrieved_chunks[:2]:
        used_sources.append(ch.source)
        txt = " ".join(ch.text.split())
        if len(txt) > 280:
            txt = txt[:280].rstrip() + "…"
        snippets.append(f"- {txt} (source: {ch.source})")

    return "Here’s what I found:\n" + "\n".join(snippets) + f"\n\n(sources: {', '.join(sorted(set(used_sources)))})"


class OllamaClient:
    """
    Minimal Ollama client. Optional: only used for INSIGHT / NEXT_STEPS.
    """
    def __init__(self, model: str = "llama3.2", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url.rstrip("/")

    def generate(self, prompt: str, temperature: float = 0.2) -> str:
        import requests
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }
        r = requests.post(url, json=payload, timeout=120)
        r.raise_for_status()
        return (r.json().get("response") or "").strip()
from pathlib import Path

def _read_context_file(filename: str) -> str:
    # robust: resolves relative to this file's location (works even if you run from elsewhere)
    base = Path(__file__).resolve().parents[2]  # project root (src/copilot/ -> src -> root)
    p = base / "context" / filename
    if not p.exists():
        raise FileNotFoundError(f"Context file not found: {p}")
    return p.read_text(encoding="utf-8", errors="ignore")


def _norm(s: str) -> str:
    # normalize: lowercase and keep only alphanumerics/spaces
    s = s.lower()
    s = "".join(ch if (ch.isalnum() or ch.isspace()) else " " for ch in s)
    return " ".join(s.split())


def _parse_md_sections(md_text: str) -> dict[str, str]:
    """
    Parses markdown into {normalized_heading: section_body}
    Supports ## and ### headings.
    """
    sections: dict[str, list[str]] = {}
    current_heading: str | None = None

    for line in md_text.splitlines():
        stripped = line.strip()

        # heading?
        if stripped.startswith("## "):
            current_heading = _norm(stripped[3:])
            sections[current_heading] = []
            continue
        if stripped.startswith("### "):
            current_heading = _norm(stripped[4:])
            sections[current_heading] = []
            continue

        if current_heading is not None:
            sections[current_heading].append(line)

    # join bodies
    return {h: "\n".join(body).strip() for h, body in sections.items() if "\n".join(body).strip()}


class CopilotAnswerer:
    def __init__(self, retriever: ContextRetriever, llm: OllamaClient | None = None):
        self.retriever = retriever
        self.llm = llm  # None allowed (then insight will be template-only)

    def answer(self, routed: RoutedQuestion, kpis: Dict[str, Any]) -> str:
        q = routed.normalized_question

        if routed.route == Route.METRIC:
            return _metric_lookup(kpis, q)

        if routed.route == Route.DEFINITION:
            # Get a few more candidates for better chance of finding the right section
            ctx = self.retriever.retrieve(q, top_k=5)
            return _format_definition_answer(q, ctx)

        # INSIGHT / NEXT_STEPS
        ctx = self.retriever.retrieve(q, top_k=3)
        metrics_block = _format_metrics(kpis)
        context_block = _format_context(ctx)

        if self.llm is None:
            # Safe fallback if Ollama not configured
            return (
                "I can help explain this, but LLM is not configured.\n\n"
                "Evidence available:\n"
                f"- Metrics keys: {', '.join(sorted(kpis.keys()))}\n"
                "Definition context:\n"
                f"{context_block}"
            )

        prompt = build_insight_prompt(metrics_block, context_block, q)
        return self.llm.generate(prompt, temperature=0.2)
