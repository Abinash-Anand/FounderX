"""Persistence boundary for pipeline outputs.

Pipeline layers call this module rather than a concrete database integration.
The orchestrator deliberately contains no enrichment, validation, or other
business decisions; the Mongo gateway owns database-specific operations.
"""

from __future__ import annotations

from typing import Any, Protocol

from app.core.settings import Settings, get_settings
from app.domain.investment_memos import InvestmentMemoArtifact
from app.domain.memos import Memo, MemoCreate
from app.integrations.mongodb import (
    EvidenceIntelligenceRecord,
    FounderProfileRecord,
    InvestmentIntelligenceRecord,
    InvestmentMemoArtifactRecord,
    ResearchRunRecord,
    build_mongodb_gateway,
)
from app.intelligence.evidence_intelligence import EvidenceIntelligence
from app.intelligence.investment_intelligence import InvestmentIntelligence
from app.intelligence.profile_models import FounderProfile, Layer1Input


class PersistenceGateway(Protocol):
    """Storage operations needed by the pipeline persistence boundary."""

    def create_research_run(
        self, payload: Layer1Input, metadata: dict[str, Any]
    ) -> ResearchRunRecord: ...

    def create_founder_profile(
        self, profile: FounderProfile, research_run_id: str | None = None
    ) -> FounderProfileRecord: ...

    def update_founder_profile(
        self,
        founder_id: str,
        profile: FounderProfile,
        research_run_id: str | None = None,
    ) -> FounderProfileRecord: ...

    def enrich_founder_with_evidence_intelligence(
        self,
        founder_id: str,
        intelligence: EvidenceIntelligence,
        audit_metadata: dict[str, Any] | None = None,
    ) -> EvidenceIntelligenceRecord: ...

    def enrich_founder_with_investment_intelligence(
        self,
        founder_id: str,
        intelligence: InvestmentIntelligence,
    ) -> InvestmentIntelligenceRecord: ...

    def create_investment_memo_artifact(
        self,
        founder_id: str,
        artifact: InvestmentMemoArtifact,
    ) -> InvestmentMemoArtifactRecord: ...

    def create_memo(self, memo: MemoCreate) -> Memo: ...


class PersistenceOrchestrator:
    """Saves pipeline outputs through the configured persistence gateway."""

    def __init__(self, gateway: PersistenceGateway):
        self._gateway = gateway

    def save_research_run(
        self, research_run: Layer1Input, metadata: dict[str, Any]
    ) -> ResearchRunRecord:
        return self._gateway.create_research_run(research_run, metadata)

    def save_founder_profile(
        self,
        founder_profile: FounderProfile,
        research_run_id: str | None = None,
    ) -> FounderProfileRecord:
        return self._gateway.create_founder_profile(founder_profile, research_run_id)

    def update_founder_profile(
        self,
        founder_id: str,
        founder_profile: FounderProfile,
        research_run_id: str | None = None,
    ) -> FounderProfileRecord:
        return self._gateway.update_founder_profile(
            founder_id, founder_profile, research_run_id
        )

    def save_evidence_intelligence(
        self,
        founder_id: str,
        intelligence: EvidenceIntelligence,
        audit_metadata: dict[str, Any] | None = None,
    ) -> EvidenceIntelligenceRecord:
        return self._gateway.enrich_founder_with_evidence_intelligence(
            founder_id, intelligence, audit_metadata
        )

    def save_investment_intelligence(
        self,
        founder_id: str,
        intelligence: InvestmentIntelligence,
    ) -> InvestmentIntelligenceRecord:
        return self._gateway.enrich_founder_with_investment_intelligence(
            founder_id, intelligence
        )

    def save_final_investment_memo(
        self,
        founder_id: str,
        artifact: InvestmentMemoArtifact,
    ) -> InvestmentMemoArtifactRecord:
        return self._gateway.create_investment_memo_artifact(founder_id, artifact)

    def save_investment_memo(self, investment_memo: MemoCreate) -> Memo:
        return self._gateway.create_memo(investment_memo)


def build_persistence_orchestrator(
    settings: Settings | None = None,
) -> PersistenceOrchestrator:
    """Build the persistence boundary with the configured Mongo gateway."""
    return PersistenceOrchestrator(build_mongodb_gateway(settings or get_settings()))