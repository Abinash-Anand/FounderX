from app.intelligence.state import DealState


def map_sourcing(state: DealState) -> dict[str, object]:
    """Map source URLs into independently researchable signal candidates."""
    mapped = [
        {"source_url": url, "summary": "Pending source extraction", "confidence": 0.25}
        for url in state["source_urls"]
    ]
    if not mapped:
        mapped.append(
            {
                "source_url": None,
                "summary": f"Research primary signals for {state['company_name']}",
                "confidence": 0.1,
            }
        )
    return {"mapped_signals": mapped}

