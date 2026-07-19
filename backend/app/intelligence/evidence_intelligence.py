"""Layer 3 evidence-intelligence output contract."""

from pydantic import BaseModel, ConfigDict, Field

from app.intelligence.contradiction_detection import Conflict
from app.intelligence.entity_confidence import EntityConfidence
from app.intelligence.evidence_reliability import EvidenceReliabilityResult
from app.intelligence.evidence_verification import ClaimVerification
from app.intelligence.profile_models import Evidence, Unknown


class EvidenceIntelligence(BaseModel):
    """Evidence-derived outputs that enrich, but never replace, Layer 2."""

    model_config = ConfigDict(extra="forbid")

    evidence: list[Evidence] = Field(default_factory=list)
    evidenceRegistry: list[Evidence] = Field(default_factory=list)
    verification: list[ClaimVerification] = Field(default_factory=list)
    reliability: list[EvidenceReliabilityResult] = Field(default_factory=list)
    entityConfidence: list[EntityConfidence] = Field(default_factory=list)
    contradictions: list[Conflict] = Field(default_factory=list)
    unknowns: list[Unknown] = Field(default_factory=list)