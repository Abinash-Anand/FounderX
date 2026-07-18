from typing import Any, TypedDict


class DealState(TypedDict):
    company_name: str
    thesis: str
    source_urls: list[str]
    mapped_signals: list[dict[str, Any]]
    signals: list[dict[str, Any]]
    scores: dict[str, float]
    diligence_notes: list[str]
    recommendation: str
    errors: list[str]

