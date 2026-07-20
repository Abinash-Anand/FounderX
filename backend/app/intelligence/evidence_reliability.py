"""Deterministic reliability scoring for evidence, never for founders."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.intelligence.evidence_verification import NOT_MENTIONED, ClaimVerification
from app.intelligence.profile_models import Evidence, FounderProfile


class ReliabilityWeights(BaseModel):
    """Configurable weights for the six evidence reliability factors."""

    model_config = ConfigDict(extra="forbid")

    sourceCredibility: float = Field(default=0.30, ge=0)
    directness: float = Field(default=0.20, ge=0)
    corroboration: float = Field(default=0.20, ge=0)
    freshness: float = Field(default=0.10, ge=0)
    identityMatch: float = Field(default=0.10, ge=0)
    claimSpecificity: float = Field(default=0.10, ge=0)

    @model_validator(mode="after")
    def require_positive_total(self) -> ReliabilityWeights:
        if sum(self.model_dump().values()) <= 0:
            raise ValueError("At least one reliability weight must be positive.")
        return self


class ReliabilityFactors(BaseModel):
    """The normalized 0-100 score for each reliability factor."""

    model_config = ConfigDict(extra="forbid")

    sourceCredibility: float
    directness: float
    corroboration: float
    freshness: float
    identityMatch: float
    claimSpecificity: float


class ReliabilityAssessment(BaseModel):
    """Source, claim, and overall reliability for one evidence item."""

    model_config = ConfigDict(extra="forbid")

    sourceReliability: float
    claimReliability: float
    overallEvidenceReliability: float
    overallScore: float
    factorBreakdown: ReliabilityFactors
    explanation: str


class EvidenceReliabilityResult(BaseModel):
    """Reliability output explicitly linked to one registry evidence ID."""

    model_config = ConfigDict(extra="forbid")

    evidenceId: str
    reliability: ReliabilityAssessment


EvidenceRegistryInput = FounderProfile | Mapping[str, Any] | Iterable[Evidence | Mapping[str, Any]]
VerificationInput = (
    Iterable[ClaimVerification | Mapping[str, Any]]
    | ClaimVerification
    | Mapping[str, Any]
)

_SOURCE_CREDIBILITY = {
    "Official Website": 90.0,
    "Government": 95.0,
    "University": 90.0,
    "Research Paper": 92.0,
    "Patent": 95.0,
    "GitHub": 80.0,
    "LinkedIn": 75.0,
    "Investor": 82.0,
    "Company Blog": 75.0,
    "News": 70.0,
    "Podcast": 65.0,
    "Conference": 70.0,
    "Social Media": 45.0,
    "Personal Website": 55.0,
    "Community": 45.0,
    "Forum": 35.0,
    "Unknown": 20.0,
}

_DIRECTNESS = {
    "Strong": 100.0,
    "Moderate": 70.0,
    "Weak": 35.0,
    NOT_MENTIONED: 0.0,
    "Contradicted": 100.0,
}

_SPECIFICITY = {
    "Strong": 90.0,
    "Moderate": 70.0,
    "Weak": 40.0,
    NOT_MENTIONED: 0.0,
    "Contradicted": 90.0,
}


def calculate_evidence_reliability(
    evidence_registry: EvidenceRegistryInput,
    evidence_classification: EvidenceRegistryInput | None = None,
    evidence_verification: VerificationInput | None = None,
    *,
    weights: ReliabilityWeights | Mapping[str, Any] | None = None,
    as_of: date | datetime | str | None = None,
) -> list[EvidenceReliabilityResult]:
    """Calculate deterministic reliability reports for every registry evidence item."""
    registry_items = _evidence_items(evidence_registry)
    registry = _index_evidence(registry_items)
    classified = _index_evidence(
        _evidence_items(evidence_classification)
        if evidence_classification is not None
        else registry_items
    )
    verifications = _verification_items(evidence_verification)
    reliability_weights = ReliabilityWeights.model_validate(weights or {})
    reference_date = _reference_date(registry.values(), as_of)

    results: list[EvidenceReliabilityResult] = []
    for evidence in registry_items:
        classified_evidence = classified.get(evidence.id, evidence)
        related = [
            item for item in verifications if evidence.id in set(item.evidenceIds)
        ]
        factors = ReliabilityFactors(
            sourceCredibility=_source_credibility(classified_evidence),
            directness=_directness_score(related),
            corroboration=_corroboration_score(related, registry),
            freshness=_freshness_score(evidence, reference_date),
            identityMatch=_identity_match(classified_evidence),
            claimSpecificity=_specificity_score(related),
        )
        source_reliability = _weighted_average(
            (
                (factors.sourceCredibility, reliability_weights.sourceCredibility),
                (factors.freshness, reliability_weights.freshness),
                (factors.identityMatch, reliability_weights.identityMatch),
            )
        )
        claim_reliability = _weighted_average(
            (
                (factors.directness, reliability_weights.directness),
                (factors.corroboration, reliability_weights.corroboration),
                (factors.claimSpecificity, reliability_weights.claimSpecificity),
            )
        )
        overall_score = _weighted_average(
            (
                (factors.sourceCredibility, reliability_weights.sourceCredibility),
                (factors.directness, reliability_weights.directness),
                (factors.corroboration, reliability_weights.corroboration),
                (factors.freshness, reliability_weights.freshness),
                (factors.identityMatch, reliability_weights.identityMatch),
                (factors.claimSpecificity, reliability_weights.claimSpecificity),
            )
        )
        results.append(
            EvidenceReliabilityResult(
                evidenceId=evidence.id,
                reliability=ReliabilityAssessment(
                    sourceReliability=_rounded(source_reliability),
                    claimReliability=_rounded(claim_reliability),
                    overallEvidenceReliability=_rounded(overall_score),
                    overallScore=_rounded(overall_score),
                    factorBreakdown=ReliabilityFactors(
                        **{
                            key: _rounded(value)
                            for key, value in factors.model_dump().items()
                        }
                    ),
                    explanation=_explanation(
                        evidence,
                        source_reliability,
                        claim_reliability,
                        overall_score,
                        related,
                    ),
                ),
            )
        )
    return results


def _evidence_items(
    source: EvidenceRegistryInput | None,
) -> list[Evidence]:
    if source is None:
        return []
    if isinstance(source, FounderProfile):
        raw_items: Iterable[Evidence | Mapping[str, Any]] = source.evidence
    elif isinstance(source, Mapping):
        raw_items = source.get("evidence", [])
    else:
        raw_items = source
    return [Evidence.model_validate(item) for item in raw_items]


def _index_evidence(items: Iterable[Evidence]) -> dict[str, Evidence]:
    indexed: dict[str, Evidence] = {}
    for item in items:
        if not item.id:
            continue
        if item.id in indexed and indexed[item.id] != item:
            raise ValueError(f"Evidence ID {item.id!r} identifies conflicting evidence.")
        indexed[item.id] = item
    return indexed


def _verification_items(source: VerificationInput | None) -> list[ClaimVerification]:
    if source is None:
        return []
    if isinstance(source, ClaimVerification):
        raw_items: Iterable[ClaimVerification | Mapping[str, Any]] = [source]
    elif isinstance(source, Mapping):
        raw_items = source.get("verifications", [source])
    else:
        raw_items = source
    return [ClaimVerification.model_validate(item) for item in raw_items]


def _source_credibility(evidence: Evidence) -> float:
    return _SOURCE_CREDIBILITY.get(evidence.sourceCategory, _SOURCE_CREDIBILITY["Unknown"])


def _directness_score(verifications: Iterable[ClaimVerification]) -> float:
    scores = [
        _DIRECTNESS[item.verification.supportStrength]
        for item in verifications
    ]
    return max(scores, default=0.0)


def _specificity_score(verifications: Iterable[ClaimVerification]) -> float:
    scores = [
        _SPECIFICITY[item.verification.supportStrength]
        for item in verifications
    ]
    return max(scores, default=0.0)


def _corroboration_score(
    verifications: Iterable[ClaimVerification],
    registry: Mapping[str, Evidence],
) -> float:
    counts = [
        len({evidence_id for evidence_id in item.evidenceIds if evidence_id in registry})
        for item in verifications
        if item.verification.supportStrength != NOT_MENTIONED
    ]
    count = max(counts, default=0)
    return {0: 0.0, 1: 50.0, 2: 75.0}.get(count, 100.0)


def _identity_match(evidence: Evidence) -> float:
    if evidence.sourceCategory == "Unknown":
        return 20.0
    if evidence.source and evidence.url:
        return 100.0
    if evidence.source or evidence.url:
        return 80.0
    return 60.0


def _reference_date(
    evidence: Iterable[Evidence],
    as_of: date | datetime | str | None,
) -> date | None:
    explicit_date = _parse_date(as_of)
    if explicit_date is not None:
        return explicit_date
    observed_dates = [
        parsed
        for item in evidence
        for parsed in (_parse_date(item.retrievedAt), _parse_date(item.publishedAt))
        if parsed is not None
    ]
    return max(observed_dates, default=None)


def _freshness_score(evidence: Evidence, reference_date: date | None) -> float:
    if reference_date is None:
        return 0.0
    observed_dates = [
        parsed
        for parsed in (_parse_date(evidence.retrievedAt), _parse_date(evidence.publishedAt))
        if parsed is not None
    ]
    if not observed_dates:
        return 0.0
    age_days = max((reference_date - max(observed_dates)).days, 0)
    if age_days <= 30:
        return 100.0
    if age_days <= 180:
        return 80.0
    if age_days <= 365:
        return 60.0
    if age_days <= 730:
        return 40.0
    return 20.0


def _parse_date(value: date | datetime | str | None) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized).date()
    except ValueError:
        try:
            return date.fromisoformat(normalized[:10])
        except ValueError:
            return None


def _weighted_average(values: Iterable[tuple[float, float]]) -> float:
    pairs = list(values)
    total_weight = sum(weight for _, weight in pairs)
    if total_weight <= 0:
        return 0.0
    return sum(value * weight for value, weight in pairs) / total_weight


def _rounded(value: float) -> float:
    return round(value, 2)


def _explanation(
    evidence: Evidence,
    source_reliability: float,
    claim_reliability: float,
    overall_score: float,
    verifications: Iterable[ClaimVerification],
) -> str:
    verification_count = len(list(verifications))
    verification_note = (
        f" Evaluated {verification_count} linked verification result(s)."
        if verification_count
        else " No linked verification result was supplied."
    )
    return (
        f"Evidence {evidence.id} scored source reliability {_rounded(source_reliability):.2f}, "
        f"claim reliability {_rounded(claim_reliability):.2f}, and overall reliability "
        f"{_rounded(overall_score):.2f}." + verification_note
    )