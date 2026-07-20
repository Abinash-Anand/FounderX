"""Direct decision-graph orchestration shared by API and pipeline callers."""

from __future__ import annotations

from typing import Any


async def evaluate_decision_state(
    *,
    company_name: str,
    thesis: str = "",
    source_urls: list[str] | None = None,
) -> dict[str, Any]:
    """Run the decision graph without making an HTTP request."""

    from app.intelligence.graph import build_decision_graph

    graph = build_decision_graph()
    return await graph.ainvoke(
        {
            "company_name": company_name,
            "thesis": thesis,
            "source_urls": source_urls or [],
            "mapped_signals": [],
            "signals": [],
            "scores": {},
            "diligence_notes": [],
            "recommendation": "pending",
            "errors": [],
        }
    )