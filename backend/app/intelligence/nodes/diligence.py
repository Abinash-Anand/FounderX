from app.intelligence.state import DealState


def run_diligence(state: DealState) -> dict[str, object]:
    """Define the evidence gaps that CrewAI and Tavily will resolve."""
    return {
        "diligence_notes": [
            "Validate founder claims against independent sources.",
            "Run a Truth-Gap Check on market size and growth claims.",
            f"Resolve {len(state['signals'])} preliminary sourcing signal(s).",
        ]
    }

