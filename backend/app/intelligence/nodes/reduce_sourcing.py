from app.intelligence.state import DealState


def reduce_sourcing(state: DealState) -> dict[str, object]:
    """Reduce mapped research into a deduplicated evidence set."""
    seen: set[tuple[object, object]] = set()
    signals: list[dict[str, object]] = []
    for signal in state["mapped_signals"]:
        key = (signal.get("source_url"), signal.get("summary"))
        if key not in seen:
            seen.add(key)
            signals.append(signal)
    return {"signals": signals}

