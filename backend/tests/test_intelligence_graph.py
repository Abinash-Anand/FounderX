import asyncio

from app.intelligence.graph import build_decision_graph


def test_decision_graph_advances_a_sourced_company() -> None:
    result = asyncio.run(
        build_decision_graph().ainvoke(
            {
                "company_name": "Example Labs",
                "thesis": "Infrastructure for autonomous finance",
                "source_urls": ["https://example.com/traction", "https://example.com/founder"],
                "mapped_signals": [],
                "signals": [],
                "scores": {},
                "diligence_notes": [],
                "recommendation": "pending",
                "errors": [],
            }
        )
    )

    assert result["recommendation"] == "advance_to_partner_review"
    assert len(result["signals"]) == 2
    assert set(result["scores"]) == {"founder", "market", "idea_market"}

