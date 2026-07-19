from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.errors import IntegrationNotConfigured
from app.core.settings import get_settings
from app.intelligence.founder_intelligence import build_founder_intelligence_service
from app.intelligence.founder_pipeline import (
    FounderAnalysisResult,
    FounderExtractionError,
    FounderIntelligenceError,
    ProfileNormalizationError,
    ResearchAgentError,
    enrich_and_persist_founder,
    run_founder_analysis,
    structure_and_persist_founder,
)
from app.intelligence.llm_normalization import OpenAIProfileClient, structure_founder_profile
from app.intelligence.profile_models import FounderProfile, Layer1Input
from app.persistence import build_persistence_orchestrator

router = APIRouter()


class AnalyzeRequest(BaseModel):
    query: str = Field(min_length=1, max_length=5_000)


@router.post(
    "/structure",
    responses={503: {"description": "OpenAI structuring integration is not configured."}},
)
async def structure_founder(payload: Layer1Input) -> FounderProfile:
    settings = get_settings()
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=503,
            detail="Founder structuring requires OPENAI_API_KEY.",
        )
    try:
        client = OpenAIProfileClient(api_key=settings.openai_api_key.get_secret_value())
        return await structure_and_persist_founder(
            payload,
            settings,
            structuring_client=client,
            structurer=structure_founder_profile,
            persistence_factory=build_persistence_orchestrator,
        )
    except IntegrationNotConfigured as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@router.post(
    "/intelligence",
    response_model=FounderProfile,
    responses={
        404: {"description": "The founder profile does not exist in persistence."},
        502: {"description": "Founder intelligence generation failed."},
        503: {"description": "OpenAI founder intelligence is not configured."},
    },
)
async def enrich_founder_intelligence(profile: FounderProfile) -> FounderProfile:
    settings = get_settings()
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=503,
            detail="Founder intelligence requires OPENAI_API_KEY.",
        )
    try:
        return await enrich_and_persist_founder(
            profile,
            settings,
            intelligence_builder=build_founder_intelligence_service,
            persistence_factory=build_persistence_orchestrator,
        )
    except IntegrationNotConfigured as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except FounderIntelligenceError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@router.post(
    "/analyze",
    response_model=FounderAnalysisResult,
    responses={
        404: {"description": "The founder profile could not be persisted."},
        502: {"description": "A founder analysis stage failed."},
        503: {"description": "A required integration is not configured."},
    },
)
async def analyze_founder(request: AnalyzeRequest) -> FounderAnalysisResult:
    try:
        return await run_founder_analysis(request.query)
    except IntegrationNotConfigured as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except (
        FounderExtractionError,
        FounderIntelligenceError,
        ProfileNormalizationError,
        ResearchAgentError,
    ) as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
