from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class Route(str, Enum):
    METRIC = "metric"
    DEFINITION = "definition"
    INSIGHT = "insight"
    NEXT_STEPS = "next_steps"


@dataclass
class RoutedQuestion:
    route: Route
    normalized_question: str


def route_question(question: str) -> RoutedQuestion:
    q = (question or "").strip().lower()

    # Buckets by intent words
    definition_triggers = ["what does", "definition", "define", "how is", "formula", "include", "exclude", "calculated"]
    insight_triggers = ["why", "reason", "driver", "explain", "root cause", "what caused"]
    next_triggers = ["next", "investigate", "recommend", "what should", "suggest", "action", "follow up"]

    if any(t in q for t in definition_triggers):
        return RoutedQuestion(Route.DEFINITION, q)
    if any(t in q for t in insight_triggers):
        return RoutedQuestion(Route.INSIGHT, q)
    if any(t in q for t in next_triggers):
        return RoutedQuestion(Route.NEXT_STEPS, q)

    # Default: metric lookup (what/how much/how many)
    return RoutedQuestion(Route.METRIC, q)
