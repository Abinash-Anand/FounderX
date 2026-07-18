from app.intelligence.state import DealState


def decide(state: DealState) -> dict[str, str]:
    """Return a conservative placeholder recommendation until diligence is complete."""
    average_score = sum(state["scores"].values()) / max(len(state["scores"]), 1)
    recommendation = "advance_to_partner_review" if average_score >= 65 else "hold_for_evidence"
    return {"recommendation": recommendation}

