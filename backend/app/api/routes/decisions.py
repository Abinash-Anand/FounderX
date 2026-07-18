from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class DecisionRequest(BaseModel):
    company_name: str = Field(min_length=1, max_length=200)
    thesis: str = Field(default="", max_length=5_000)
    source_urls: list[str] = Field(default_factory=list, max_length=20)


class DecisionResponse(BaseModel):
    company_name: str
    recommendation: str
    state: dict[str, Any]


@router.post("/evaluate", response_model=DecisionResponse)
async def evaluate_deal(request: DecisionRequest) -> DecisionResponse:
    # Imported on demand so the health route does not pay LangGraph's import cost.
    from app.intelligence.graph import build_decision_graph

    graph = build_decision_graph()
    state = await graph.ainvoke(
        {
            "company_name": request.company_name,
            "thesis": request.thesis,
            "source_urls": request.source_urls,
            "mapped_signals": [],
            "signals": [],
            "scores": {},
            "diligence_notes": [],
            "recommendation": "pending",
            "errors": [],
        }
    )
    return DecisionResponse(
        company_name=request.company_name,
        recommendation=state["recommendation"],
        state=state,
    )

