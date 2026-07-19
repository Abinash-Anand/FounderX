"""Deterministic confidence aggregation for profile entities only."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.intelligence.evidence_reliability import EvidenceReliabilityResult
from app.intelligence.profile_models import FounderProfile


class ConfidenceBreakdown(BaseModel):
    """Evidence aggregation factors contributing to entity confidence."""

    model_config = ConfigDict(extra="forbid")

    strongestEvidence: float
    averageEvidence: float
    weakestEvidence: float
    corroboration: float
    coverage: float


class EntityConfidence(BaseModel):
    """Confidence report for one non-founder profile entity."""

    model_config = ConfigDict(extra="forbid")

    entityType: str
    entityId: str
    confidence: float
    supportingEvidence: list[str] = Field(default_factory=list)
    strongestEvidence: str = ""
    weakestEvidence: str = ""
    confidenceBreakdown: ConfidenceBreakdown
    coverage: float


ReliabilityInput = (
    Iterable[EvidenceReliabilityResult | Mapping[str, Any]]
    | EvidenceReliabilityResult
    | Mapping[str, Any]
)

_ENTITY_COLLECTIONS = (
    ("education", "education"),
    ("experience", "experience"),
    ("startupHistory", "startup"),
    ("projects", "project"),
    ("patents", "patent"),
    ("awards", "award"),
    ("research", "publication"),
)


def calculate_entity_confidence(
    profile: FounderProfile | Mapping[str, Any],
    evidence_reliability: ReliabilityInput,
) -> list[EntityConfidence]:
    """Aggregate registered evidence reliability for every supported entity."""
    canonical_profile = FounderProfile.model_validate(profile)
    reliability_by_id = _reliability_index(evidence_reliability)
    results: list[EntityConfidence] = []

    for collection_name, entity_type in _ENTITY_COLLECTIONS:
        entities = getattr(canonical_profile, collection_name)
        for index, entity in enumerate(entities):
            entity_data = entity.model_dump(mode="python")
            entity_id = entity_data.get("id") or f"{entity_type}-{index + 1}"
            linked_ids = _unique_ids(entity_data.get("evidenceIds", []))
            supporting_ids = [
                evidence_id for evidence_id in linked_ids if evidence_id in reliability_by_id
            ]
            scores = [reliability_by_id[evidence_id] for evidence_id in supporting_ids]
            coverage = _coverage(len(supporting_ids), len(linked_ids))
            results.append(
                _build_entity_confidence(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    supporting_ids=supporting_ids,
                    scores=scores,
                    coverage=coverage,
                )
            )
    return results


def _reliability_index(source: ReliabilityInput) -> dict[str, float]:
    if isinstance(source, EvidenceReliabilityResult):
        raw_items: Iterable[EvidenceReliabilityResult | Mapping[str, Any]] = [source]
    elif isinstance(source, Mapping):
        raw_items = source.get("results", [source])
    else:
        raw_items = source

    index: dict[str, float] = {}
    for raw_item in raw_items:
        item = EvidenceReliabilityResult.model_validate(raw_item)
        if item.evidenceId in index and index[item.evidenceId] != item.reliability.overallScore:
            raise ValueError(
                f"Evidence ID {item.evidenceId!r} has conflicting reliability results."
            )
        index[item.evidenceId] = item.reliability.overallScore
    return index


def _build_entity_confidence(
    *,
    entity_type: str,
    entity_id: str,
    supporting_ids: list[str],
    scores: list[float],
    coverage: float,
) -> EntityConfidence:
    if not scores:
        breakdown = ConfidenceBreakdown(
            strongestEvidence=0.0,
            averageEvidence=0.0,
            weakestEvidence=0.0,
            corroboration=0.0,
            coverage=coverage,
        )
        return EntityConfidence(
            entityType=entity_type,
            entityId=entity_id,
            confidence=0.0,
            supportingEvidence=supporting_ids,
            confidenceBreakdown=breakdown,
            coverage=coverage,
        )

    evidence_scores = dict(zip(supporting_ids, scores, strict=True))
    strongest_id = min(
        evidence_scores,
        key=lambda evidence_id: (-evidence_scores[evidence_id], evidence_id),
    )
    weakest_id = min(
        evidence_scores,
        key=lambda evidence_id: (evidence_scores[evidence_id], evidence_id),
    )
    strongest = evidence_scores[strongest_id]
    weakest = evidence_scores[weakest_id]
    average = sum(scores) / len(scores)
    corroboration = min(len(scores), 3) / 3 * 100
    quality = (strongest * 0.60) + (average * 0.40)
    corroboration_bonus = min(max(len(scores) - 1, 0) * 5, 15)
    confidence = min(100.0, (quality + corroboration_bonus) * coverage / 100)
    breakdown = ConfidenceBreakdown(
        strongestEvidence=_rounded(strongest),
        averageEvidence=_rounded(average),
        weakestEvidence=_rounded(weakest),
        corroboration=_rounded(corroboration),
        coverage=_rounded(coverage),
    )
    return EntityConfidence(
        entityType=entity_type,
        entityId=entity_id,
        confidence=_rounded(confidence),
        supportingEvidence=supporting_ids,
        strongestEvidence=strongest_id,
        weakestEvidence=weakest_id,
        confidenceBreakdown=breakdown,
        coverage=_rounded(coverage),
    )


def _unique_ids(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    result: list[str] = []
    for value in values:
        if isinstance(value, str) and value and value not in result:
            result.append(value)
    return result


def _coverage(supporting_count: int, linked_count: int) -> float:
    if linked_count == 0:
        return 0.0
    return supporting_count / linked_count * 100


def _rounded(value: float) -> float:
    return round(value, 2)