"""Deterministic contradiction detection for scoped structured claims."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from hashlib import sha256
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.intelligence.evidence_verification import VerificationClaim

ConflictSeverity = Literal["Low", "Medium", "High"]


class ConflictValue(BaseModel):
    """One distinct value in a detected conflict and its evidence links."""

    model_config = ConfigDict(extra="forbid")

    value: str
    supportingEvidence: list[str] = Field(default_factory=list)
    claimIds: list[str] = Field(default_factory=list)


class ConflictReview(BaseModel):
    """Review metadata for an unresolved conflict."""

    model_config = ConfigDict(extra="forbid")

    required: bool = True
    status: Literal["needs_review"] = "needs_review"
    reason: str


class Conflict(BaseModel):
    """A reviewable contradiction with no automatically selected value."""

    model_config = ConfigDict(extra="forbid")

    conflictId: str
    entityType: str
    entityId: str
    field: str
    values: list[ConflictValue]
    supportingEvidence: list[str] = Field(default_factory=list)
    severity: ConflictSeverity
    review: ConflictReview


ClaimInput = Iterable[VerificationClaim | Mapping[str, Any]]

_HIGH_IMPACT_FIELDS = {
    "company",
    "companyname",
    "enddate",
    "founded",
    "foundingyear",
    "funding",
    "institution",
    "startdate",
    "title",
}


def detect_contradictions(claims: ClaimInput) -> list[Conflict]:
    """Cluster conflicting values while preserving every claim and evidence link."""
    groups: dict[tuple[str, str, str], dict[str, Any]] = {}
    for raw_claim in claims:
        claim = VerificationClaim.model_validate(raw_claim)
        if not claim.value.strip():
            continue
        entity_type = _normalize(claim.entityType)
        entity_id = _normalize(claim.entityId)
        field_key = _normalize(claim.field)
        group_key = (entity_type, entity_id, field_key)
        value_key = _normalize(claim.value)
        group = groups.setdefault(
            group_key,
            {
                "entityType": claim.entityType,
                "entityId": claim.entityId,
                "field": claim.field,
                "values": {},
            },
        )
        value_entry = group["values"].setdefault(
            value_key,
            {"value": claim.value, "evidence": [], "claims": []},
        )
        _append_unique(value_entry["evidence"], claim.evidenceIds)
        claim_id = claim.id or _generated_claim_id(claim)
        _append_unique(value_entry["claims"], [claim_id])

    conflicts: list[Conflict] = []
    for group_key in sorted(groups):
        group = groups[group_key]
        values_by_key = group["values"]
        if len(values_by_key) < 2:
            continue
        entity_type = group["entityType"]
        entity_id = group["entityId"]
        field = group["field"]
        values = [
            ConflictValue(
                value=entry["value"],
                supportingEvidence=entry["evidence"],
                claimIds=entry["claims"],
            )
            for _, entry in values_by_key.items()
        ]
        supporting_evidence = _unique(
            evidence_id
            for value in values
            for evidence_id in value.supportingEvidence
        )
        severity = _severity(group_key[2], len(supporting_evidence))
        conflict_id = _conflict_id(*group_key, values_by_key)
        conflicts.append(
            Conflict(
                conflictId=conflict_id,
                entityType=entity_type,
                entityId=entity_id,
                field=field,
                values=values,
                supportingEvidence=supporting_evidence,
                severity=severity,
                review=ConflictReview(
                    reason="Conflicting values were detected; no value was selected automatically."
                ),
            )
        )
    return conflicts


def detect_conflicts(claims: ClaimInput) -> list[Conflict]:
    """Alias for callers that use the shorter conflict-detection name."""
    return detect_contradictions(claims)


def _severity(field: str, evidence_count: int) -> ConflictSeverity:
    if evidence_count >= 2 and field in _HIGH_IMPACT_FIELDS:
        return "High"
    if evidence_count >= 1:
        return "Medium"
    return "Low"


def _conflict_id(
    entity_type: str,
    entity_id: str,
    field: str,
    values: Mapping[str, Mapping[str, Any]],
) -> str:
    identity = "|".join((entity_type, entity_id, field, *sorted(values)))
    return f"conflict-{sha256(identity.encode('utf-8')).hexdigest()[:16]}"


def _generated_claim_id(claim: VerificationClaim) -> str:
    identity = "|".join((claim.entityType, claim.entityId, claim.field, claim.value))
    return f"claim-{sha256(identity.encode('utf-8')).hexdigest()[:16]}"


def _normalize(value: str) -> str:
    return " ".join(re.findall(r"[\w]+", value.casefold()))


def _append_unique(target: list[str], values: Iterable[str]) -> None:
    for value in values:
        if value and value not in target:
            target.append(value)


def _unique(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    _append_unique(result, values)
    return result