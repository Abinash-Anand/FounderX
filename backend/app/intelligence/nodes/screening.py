from app.intelligence.state import DealState


def screen(state: DealState) -> dict[str, object]:
    """Produce placeholder multi-axis scores from the current evidence set."""
    evidence_bonus = min(len(state["signals"]) * 2.5, 10)
    return {
        "scores": {
            "founder": 60 + evidence_bonus,
            "market": 60 + evidence_bonus,
            "idea_market": 60 + evidence_bonus,
        }
    }

