from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.errors import IntegrationNotConfigured
from app.intelligence.founder_extraction import (
    FounderExtractionError,
    FounderIntelligenceBatch,
    build_founder_extraction_agent,
)
from app.intelligence.identifiers import ensure_layer1_founder_identifier
from app.intelligence.profile_models import Layer1Input
from app.intelligence.research_agent import (
    ResearchAgentError,
    build_vc_research_agent,
)
from app.intelligence.search_planner import (
    SearchPlan,
    SearchPlanningError,
    build_search_planner,
)
from app.persistence import build_persistence_orchestrator

router = APIRouter()


class ResearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=5_000)


class ExtractionRequest(BaseModel):
    search_results: list[dict[str, Any]] = Field(min_length=1, max_length=50)


class ResearchQueryResponse(Layer1Input):
    researchRunId: str


@router.post(
    "/extract",
    responses={
        502: {"description": "The extraction provider failed or returned invalid data."},
        503: {"description": "OpenAI founder extraction is not configured."},
    },
)
async def extract_founder_intelligence(
    request: ExtractionRequest,
) -> FounderIntelligenceBatch:
    try:
        agent = build_founder_extraction_agent()
        return await agent.extract(request.search_results)
    except IntegrationNotConfigured as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except FounderExtractionError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@router.post(
    "/plan",
    responses={
        502: {"description": "The search planner failed or returned invalid data."},
        503: {"description": "OpenAI search planning integration is not configured."},
    },
)
async def plan_vc_query(request: ResearchRequest) -> SearchPlan:
    try:
        planner = build_search_planner()
        return await planner.plan(request.query)
    except IntegrationNotConfigured as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except SearchPlanningError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@router.post(
    "/query",
    responses={
        502: {"description": "The research provider failed or returned invalid data."},
        503: {"description": "OpenAI or Tavily research integration is not configured."},
    },
)
async def research_vc_query(request: ResearchRequest) -> ResearchQueryResponse:
    try:
        agent = build_vc_research_agent()
        payload = ensure_layer1_founder_identifier(await agent.research(request.query))
        persistence = build_persistence_orchestrator()
        metadata = {
            "query": request.query,
            "source": "research-route",
            "createdAt": datetime.now(UTC).isoformat(),
            "founderId": payload.metadata.founderId,
        }
        stored_run = persistence.save_research_run(payload, metadata)
        return ResearchQueryResponse(
            researchRunId=stored_run.researchRunId,
            **payload.model_dump(mode="json"),
        )
    except IntegrationNotConfigured as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ResearchAgentError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
