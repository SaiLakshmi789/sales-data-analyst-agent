SYSTEM_RULES = """You are an Analytics Copilot.
Use ONLY the provided numeric metrics and retrieved context.
Never invent numbers. If a value is not available, say you don't have it.
When you use context, cite the source file like (source: kpi_definitions.md).
Keep the answer concise and business-friendly.
"""

def build_insight_prompt(metrics_block: str, context_block: str, question: str) -> str:
    return f"""{SYSTEM_RULES}

NUMERIC METRICS (ground truth):
{metrics_block}

RETRIEVED CONTEXT (definitions/rules/caveats):
{context_block}

USER QUESTION:
{question}

Write:
1) Direct answer (1-2 lines)
2) Evidence (reference metrics + cite sources)
3) Likely drivers (ranked)
4) Next checks (3 bullets, grounded)
"""
