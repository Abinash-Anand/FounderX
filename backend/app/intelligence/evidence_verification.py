"""Deterministic verification of structured claims against supplied evidence."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.intelligence.profile_models import Evidence, FounderProfile

NOT_MENTIONED = "Not Mentioned"
SupportStrength = Literal["Strong", "Moderate", "Weak", NOT_MENTIONED, "Contradicted"]
SupportType = Literal["Primary", "Secondary", "Inferred", "Quoted"]


class VerificationClaim(BaseModel):
    """A structured claim and the registry evidence selected for verification."""

    model_config = ConfigDict(extra="forbid")

    id: str = ""
    entityType: str = ""
    entityId: str = ""
    field: str = ""
    value: str = ""
    text: str = ""
    evidenceIds: list[str] = Field(default_factory=list)


class Verification(BaseModel):
    """The factual verification result for one claim-evidence set."""

    model_config = ConfigDict(extra="forbid")

    supportStrength: SupportStrength
    supportType: SupportType
    reasoning: str
    limitations: list[str] = Field(default_factory=list)


class ClaimVerification(BaseModel):
    """A verification result explicitly linked back to its claim and evidence."""

    model_config = ConfigDict(extra="forbid")

    claimId: str
    evidenceIds: list[str] = Field(default_factory=list)
    verification: Verification


EvidenceRegistryInput = (
    FounderProfile | Mapping[str, Any] | Iterable[Evidence | Mapping[str, Any]]
)


def verify_claim(
    claim: VerificationClaim | Mapping[str, Any],
    evidence_registry: EvidenceRegistryInput,
) -> Verification:
    """Verify one claim against only the evidence IDs attached to it."""
    claim_model = VerificationClaim.model_validate(claim)
    evidence_by_id = _build_evidence_index(evidence_registry)
    return _verify_claim(claim_model, evidence_by_id)


def verify_claims(
    claims: Iterable[VerificationClaim | Mapping[str, Any]],
    evidence_registry: EvidenceRegistryInput,
) -> list[ClaimVerification]:
    """Verify every supplied claim and keep each result explicitly linked."""
    evidence_by_id = _build_evidence_index(evidence_registry)
    results: list[ClaimVerification] = []
    for raw_claim in claims:
        claim = VerificationClaim.model_validate(raw_claim)
        claim_id = claim.id or _generated_claim_id(claim)
        results.append(
            ClaimVerification(
                claimId=claim_id,
                evidenceIds=list(claim.evidenceIds),
                verification=_verify_claim(claim, evidence_by_id),
            )
        )
    return results


def _verify_claim(
    claim: VerificationClaim,
    evidence_by_id: Mapping[str, Evidence],
) -> Verification:
    if not claim.evidenceIds:
        return Verification(
            supportStrength=NOT_MENTIONED,
            supportType="Inferred",
            reasoning="No linked evidence was supplied for the claim.",
            limitations=["The claim has no evidence IDs to verify."],
        )

    observations: list[_Observation] = []
    limitations: list[str] = []
    for evidence_id in sorted(set(claim.evidenceIds)):
        evidence = evidence_by_id.get(evidence_id)
        if evidence is None:
            limitations.append(f"Evidence ID {evidence_id!r} was not found in the registry.")
            continue
        observations.append(
            _Observation(
                evidence_id=evidence_id,
                verification=_verify_against_evidence(claim, evidence),
            )
        )

    if not observations:
        return Verification(
            supportStrength=NOT_MENTIONED,
            supportType="Inferred",
            reasoning="None of the linked evidence IDs exists in the registry.",
            limitations=limitations,
        )
    selected = _select_observation(observations)
    return Verification(
        supportStrength=selected.verification.supportStrength,
        supportType=selected.verification.supportType,
        reasoning=selected.verification.reasoning,
        limitations=_unique_strings(
            [*selected.verification.limitations, *limitations]
        ),
    )


def _verify_against_evidence(claim: VerificationClaim, evidence: Evidence) -> Verification:
    text = _evidence_text(evidence)
    claim_text = _normalize(claim.text)
    claim_value = _normalize(claim.value)
    field_supported = _field_is_supported(claim.field, evidence.supports)
    source_type = _source_support_type(evidence)

    if text and claim_value and field_supported and _is_negated(text, claim_value):
        return Verification(
            supportStrength="Contradicted",
            supportType=_quoted_or_source_type(claim_value, evidence, source_type),
            reasoning="The supplied evidence explicitly negates the claimed value.",
            limitations=[],
        )
    if text and claim_text and _contains_phrase(text, claim_text):
        return Verification(
            supportStrength="Strong",
            supportType=_quoted_or_source_type(claim_text, evidence, source_type),
            reasoning="The supplied evidence states the claim text verbatim.",
            limitations=[],
        )
    if text and claim_value and field_supported and _contains_phrase(text, claim_value):
        return Verification(
            supportStrength="Strong",
            supportType=source_type,
            reasoning=f"The evidence explicitly states the value for {claim.field!r}.",
            limitations=[],
        )
    if text and claim_value and _contains_phrase(text, claim_value):
        return Verification(
            supportStrength="Moderate",
            supportType=source_type,
            reasoning=(
                "The evidence mentions the claimed value but does not map it to the claim field."
            ),
            limitations=["The evidence does not declare support for the supplied claim field."],
        )
    if text and claim_value and field_supported and _contains_all_terms(text, claim_value):
        return Verification(
            supportStrength="Weak",
            supportType="Inferred",
            reasoning="The evidence contains the claim terms without an explicit statement.",
            limitations=["The claim is inferred from separate terms rather than stated verbatim."],
        )
    limitations = ["The supplied evidence does not state the claim."]
    if not text:
        limitations.insert(0, "No evidence content, excerpt, or quote was supplied.")
    return Verification(
        supportStrength=NOT_MENTIONED,
        supportType=source_type,
        reasoning="The supplied evidence does not mention the claim.",
        limitations=limitations,
    )


@dataclass(frozen=True)
class _Observation:
    evidence_id: str
    verification: Verification


def _select_observation(observations: list[_Observation]) -> _Observation:
    strength_rank = {
        "Contradicted": 5,
        "Strong": 4,
        "Moderate": 3,
        "Weak": 2,
        NOT_MENTIONED: 1,
    }
    return max(
        observations,
        key=lambda item: (strength_rank[item.verification.supportStrength], item.evidence_id),
    )


def _build_evidence_index(source: EvidenceRegistryInput) -> dict[str, Evidence]:
    if isinstance(source, FounderProfile):
        raw_evidence: Iterable[Evidence | Mapping[str, Any]] = source.evidence
    elif isinstance(source, Mapping):
        raw_evidence = source.get("evidence", [])
    else:
        raw_evidence = source

    index: dict[str, Evidence] = {}
    for raw_item in raw_evidence:
        evidence = Evidence.model_validate(raw_item)
        if not evidence.id:
            continue
        if evidence.id in index and index[evidence.id] != evidence:
            raise ValueError(f"Evidence ID {evidence.id!r} identifies conflicting evidence.")
        index[evidence.id] = evidence
    return index


def _evidence_text(evidence: Evidence) -> str:
    return _normalize(" ".join((evidence.content, evidence.excerpt, evidence.quote)))


def _field_is_supported(field: str, supports: list[str]) -> bool:
    normalized_field = _normalize(field)
    return bool(normalized_field) and any(
        _normalize(supported_field) == normalized_field for supported_field in supports
    )


def _source_support_type(evidence: Evidence) -> SupportType:
    primary_categories = {
        "Official Website",
        "Government",
        "University",
        "Research Paper",
        "Patent",
        "GitHub",
        "LinkedIn",
        "Investor",
        "Company Blog",
        "Personal Website",
    }
    return "Primary" if evidence.sourceCategory in primary_categories else "Secondary"


def _quoted_or_source_type(
    claim_text: str,
    evidence: Evidence,
    source_type: SupportType,
) -> SupportType:
    quoted_text = _normalize(" ".join((evidence.excerpt, evidence.quote)))
    return "Quoted" if _contains_phrase(quoted_text, claim_text) else source_type


def _is_negated(text: str, value: str) -> bool:
    value_pattern = re.escape(value)
    patterns = (
        rf"\b(?:not|never|no|denies|denied|false|incorrect)\b(?:\s+\w+){{0,8}}\s+{value_pattern}\b",
        rf"\b{value_pattern}\b(?:\s+\w+){{0,8}}\s+\b(?:not|never|false|incorrect)\b",
    )
    return any(re.search(pattern, text) for pattern in patterns)


def _contains_phrase(text: str, phrase: str) -> bool:
    return bool(phrase) and phrase in text


def _contains_all_terms(text: str, phrase: str) -> bool:
    terms = [term for term in phrase.split() if len(term) > 2]
    return len(terms) > 1 and all(term in text for term in terms)


def _normalize(value: str) -> str:
    return " ".join(re.findall(r"[\w]+", value.casefold()))


def _unique_strings(values: Iterable[str]) -> list[str]:
    unique: list[str] = []
    for value in values:
        if value not in unique:
            unique.append(value)
    return unique


def _generated_claim_id(claim: VerificationClaim) -> str:
    identity = "|".join((claim.field, claim.value, claim.text, *sorted(claim.evidenceIds)))
    return f"claim-{sha256(identity.encode('utf-8')).hexdigest()[:16]}"