"""Reusable founder pipeline stages and end-to-end analysis coordinator."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.core.errors import IntegrationNotConfigured
from app.core.settings import Settings, get_settings
from app.intelligence.decision_service import evaluate_decision_state
from app.intelligence.founder_extraction import (
    FounderExtractionError,
    FounderIntelligenceBatch,
    build_founder_extraction_agent,
)
from app.intelligence.founder_intelligence import (
    FounderIntelligenceError,
    build_founder_intelligence_service,
)
from app.intelligence.identifiers import (
    ensure_founder_profile_identifiers,
    ensure_layer1_founder_identifier,
    founder_identifier_for_query,
)
from app.intelligence.llm_normalization import (
    OpenAIProfileClient,
    ProfileNormalizationError,
    structure_founder_profile,
)
from app.intelligence.profile_models import FounderIntelligence, FounderProfile, Layer1Input
from app.intelligence.research_agent import ResearchAgentError, build_vc_research_agent
from app.persistence import PersistenceOrchestrator, build_persistence_orchestrator


class FounderAnalysisResult(BaseModel):
    """Final response returned by the single-call founder analysis endpoint."""

    model_config = ConfigDict(extra="forbid")

    metadata: dict[str, Any]
    research: dict[str, Any]
    founderProfile: FounderProfile
    founderIntelligence: FounderIntelligence
    investmentDecision: dict[str, Any]


async def structure_and_persist_founder(
    payload: Layer1Input,
    settings: Settings | Any | None = None,
    persistence: PersistenceOrchestrator | None = None,
    *,
    structuring_client: Any | None = None,
    structurer: Any | None = None,
    persistence_factory: Any | None = None,
) -> FounderProfile:
    """Structure Layer 1 data, assign IDs, and upsert the founder profile."""

    settings = settings or get_settings()
    if not settings.openai_api_key:
        raise IntegrationNotConfigured("Founder structuring requires OPENAI_API_KEY.")

    client = structuring_client or OpenAIProfileClient(
        api_key=settings.openai_api_key.get_secret_value()
    )
    profile = ensure_founder_profile_identifiers(
        await (structurer or structure_founder_profile)(payload, client),
        payload.metadata.founderId,
    )
    research_run_id = str(payload.model_extra.get("researchRunId", ""))
    persistence = persistence or (
        persistence_factory(settings)
        if persistence_factory
        else build_persistence_orchestrator(settings)
    )
    record = persistence.save_founder_profile(profile, research_run_id or None)
    return profile.model_copy(
        update={
            "metadata": profile.metadata.model_copy(
                update={"lastUpdated": record.updatedAt}
            ),
            "profileVersion": record.version,
        }
    )


async def enrich_and_persist_founder(
    profile: FounderProfile,
    settings: Settings | Any | None = None,
    persistence: PersistenceOrchestrator | None = None,
    *,
    intelligence_builder: Any | None = None,
    persistence_factory: Any | None = None,
) -> FounderProfile:
    """Generate Layer 3 intelligence and update the same founder document."""

    settings = settings or get_settings()
    if not settings.openai_api_key:
        raise IntegrationNotConfigured("Founder intelligence requires OPENAI_API_KEY.")

    profile = ensure_founder_profile_identifiers(profile)
    service = (intelligence_builder or build_founder_intelligence_service)(settings)
    intelligence = await service.enrich(profile)
    persistence = persistence or (
        persistence_factory(settings)
        if persistence_factory
        else build_persistence_orchestrator(settings)
    )
    try:
        record = persistence.save_founder_intelligence(profile.founder.id, intelligence)
    except KeyError:
        persistence.save_founder_profile(profile)
        record = persistence.save_founder_intelligence(profile.founder.id, intelligence)

    return profile.model_copy(
        update={
            "founderIntelligence": intelligence,
            "metadata": profile.metadata.model_copy(
                update={"lastUpdated": record.updatedAt or datetime.now(UTC).isoformat()}
            ),
            "profileVersion": record.version,
        }
    )


async def run_founder_analysis(
    query: str,
    settings: Settings | Any | None = None,
) -> FounderAnalysisResult:
    """Run research, extraction, structuring, intelligence, and decision stages."""

    settings = settings or get_settings()
    persistence = build_persistence_orchestrator(settings)

    research_agent = build_vc_research_agent(settings, include_extractor=False)
    research_payload = ensure_layer1_founder_identifier(
        await research_agent.research(query),
        founder_identifier_for_query(query),
    )
    research_metadata = {
        "query": query,
        "source": "founder-analysis-route",
        "createdAt": datetime.now(UTC).isoformat(),
        "founderId": research_payload.metadata.founderId,
    }
    stored_run = persistence.save_research_run(research_payload, research_metadata)

    extraction_agent = build_founder_extraction_agent(settings)
    extraction = await extraction_agent.extract(_extraction_input(research_payload))
    structure_payload = _attach_extraction(research_payload, extraction)
    structure_payload = structure_payload.model_copy(
        update={"researchRunId": stored_run.researchRunId}
    )
    profile = await structure_and_persist_founder(
        structure_payload,
        settings,
        persistence,
    )
    enriched_profile = await enrich_and_persist_founder(profile, settings, persistence)

    company_name = _company_name(extraction, enriched_profile, query)
    source_urls = _source_urls(extraction, research_payload)
    decision_state = await evaluate_decision_state(
        company_name=company_name,
        thesis=query,
        source_urls=source_urls,
    )
    intelligence = enriched_profile.founderIntelligence or FounderIntelligence()
    return FounderAnalysisResult(
        metadata={
            "researchRunId": stored_run.researchRunId,
            "founderId": enriched_profile.founder.id,
            "profileVersion": enriched_profile.profileVersion,
        },
        research={
            **research_payload.model_dump(mode="json"),
            "researchRunId": stored_run.researchRunId,
        },
        founderProfile=enriched_profile,
        founderIntelligence=intelligence,
        investmentDecision={
            "company_name": company_name,
            "recommendation": decision_state["recommendation"],
            "state": decision_state,
        },
    )


def _extraction_input(payload: Layer1Input) -> list[dict[str, Any]]:
    searches = payload.tavily.get("searches")
    if isinstance(searches, list) and searches:
        return [
            {
                "assistantSummary": payload.tavily.get("summary", ""),
                "searchResults": searches,
            }
        ]
    return [payload.tavily or {"layer1": payload.model_dump(mode="json")}]


def _attach_extraction(
    payload: Layer1Input,
    extraction: FounderIntelligenceBatch,
) -> Layer1Input:
    tavily = dict(payload.tavily)
    tavily["founderExtraction"] = extraction.model_dump(mode="json")
    return payload.model_copy(update={"tavily": tavily})


def _company_name(
    extraction: FounderIntelligenceBatch,
    profile: FounderProfile,
    query: str,
) -> str:
    for founder in extraction.founders:
        if founder.startup:
            return founder.startup
    return profile.founder.currentCompany or query.strip()


def _source_urls(
    extraction: FounderIntelligenceBatch,
    payload: Layer1Input,
) -> list[str]:
    urls = [
        source.url
        for founder in extraction.founders
        for source in founder.sources or []
        if source.url
    ]
    for search in payload.tavily.get("searches", []):
        if isinstance(search, dict):
            for source in search.get("sources", []):
                if isinstance(source, dict) and source.get("url"):
                    urls.append(str(source["url"]))
    return list(dict.fromkeys(urls))


__all__ = [
    "FounderAnalysisResult",
    "FounderIntelligenceError",
    "ProfileNormalizationError",
    "ResearchAgentError",
    "FounderExtractionError",
    "run_founder_analysis",
    "structure_and_persist_founder",
    "enrich_and_persist_founder",
]