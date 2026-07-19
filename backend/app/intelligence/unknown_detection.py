"""Deterministic detection of observable founder-profile information gaps."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from app.intelligence.evidence_verification import NOT_MENTIONED, ClaimVerification
from app.intelligence.profile_models import FounderProfile, Unknown

VerificationInput = (
    Iterable[ClaimVerification | Mapping[str, Any]]
    | ClaimVerification
    | Mapping[str, Any]
    | None
)

_ENTITY_COLLECTIONS = (
    ("education", "education", "Education"),
    ("experience", "experience", "Experience"),
    ("startupHistory", "startup", "Startup"),
    ("projects", "project", "Project"),
    ("repositories", "repository", "Repository"),
    ("patents", "patent", "Patent"),
    ("awards", "award", "Award"),
    ("research", "publication", "Publication"),
)

_DATE_FIELDS = {
    "education": ("startDate", "endDate"),
    "experience": ("startDate", "endDate"),
    "startupHistory": ("startDate", "endDate"),
    "projects": ("startDate", "endDate"),
    "research": ("year",),
    "publicSpeaking": ("date",),
    "awards": ("date",),
    "grants": ("date",),
    "patents": ("date",),
    "productLaunches": ("launchDate",),
}


def detect_unknowns(
    profile: FounderProfile | Mapping[str, Any],
    verifications: VerificationInput = None,
) -> list[Unknown]:
    """Return existing and newly observed unknowns without changing the profile."""
    canonical_profile = FounderProfile.model_validate(profile)
    unknowns: list[Unknown] = []
    seen: set[tuple[str, str, str, str]] = set()

    for existing in canonical_profile.unknowns:
        _add_unknown(
            unknowns,
            seen,
            category=existing.category or "existing_unknown",
            field=existing.field,
            reason=existing.reason or "The profile marked this information as unknown.",
            priority=existing.priority or _priority_from_importance(existing.importance),
            recommended_action=(
                existing.recommendedAction
                or "Investigate the reported information gap using a primary source."
            ),
            entity_type=existing.entityType,
            entity_id=existing.entityId,
        )

    if not canonical_profile.evidence:
        _add_unknown(
            unknowns,
            seen,
            category="missing_evidence",
            field="evidence",
            reason="The profile contains no registered evidence sources.",
            priority="High",
            recommended_action="Collect primary source documents and register their citations.",
        )

    for collection_name, entity_type, label in _ENTITY_COLLECTIONS:
        entities = getattr(canonical_profile, collection_name)
        if not entities:
            _add_unknown(
                unknowns,
                seen,
                category="missing_entity",
                field=collection_name,
                reason=f"No {label.lower()} entities are present in the profile.",
                priority="Medium",
                recommended_action=(
                    f"Search source documents and public records for {label.lower()} history."
                ),
                entity_type=entity_type,
            )
            continue
        for index, entity in enumerate(entities):
            _inspect_entity(
                unknowns,
                seen,
                collection_name,
                entity_type,
                index,
                entity.model_dump(mode="python"),
            )

    _inspect_dates(canonical_profile, unknowns, seen)
    _inspect_funding(canonical_profile, unknowns, seen)
    _inspect_technical_background(canonical_profile, unknowns, seen)
    _inspect_repositories(canonical_profile, unknowns, seen)
    _inspect_timeline(canonical_profile, unknowns, seen)
    _inspect_verifications(verifications, unknowns, seen)
    return unknowns


def _inspect_entity(
    unknowns: list[Unknown],
    seen: set[tuple[str, str, str, str]],
    collection_name: str,
    entity_type: str,
    index: int,
    entity: Mapping[str, Any],
) -> None:
    entity_id = str(entity.get("id") or f"{entity_type}-{index + 1}")
    evidence_ids = entity.get("evidenceIds")
    if isinstance(evidence_ids, list) and not evidence_ids:
        _add_unknown(
            unknowns,
            seen,
            category="missing_evidence",
            field=f"{collection_name}[{index}].evidenceIds",
            reason="The entity has no linked evidence IDs.",
            priority="High",
            recommended_action=(
                "Find a source that directly documents this entity and link its evidence ID."
            ),
            entity_type=entity_type,
            entity_id=entity_id,
        )


def _inspect_dates(
    profile: FounderProfile,
    unknowns: list[Unknown],
    seen: set[tuple[str, str, str, str]],
) -> None:
    for collection_name, date_fields in _DATE_FIELDS.items():
        for index, entity in enumerate(getattr(profile, collection_name)):
            data = entity.model_dump(mode="python")
            entity_type = collection_name
            entity_id = str(data.get("id") or f"{entity_type}-{index + 1}")
            for field in date_fields:
                if _is_empty(data.get(field)):
                    _add_unknown(
                        unknowns,
                        seen,
                        category="missing_date",
                        field=f"{collection_name}[{index}].{field}",
                        reason=f"The entity has no {field} recorded.",
                        priority="Medium",
                        recommended_action=(
                            f"Locate a dated primary source for the entity's {field}."
                        ),
                        entity_type=entity_type,
                        entity_id=entity_id,
                    )


def _inspect_funding(
    profile: FounderProfile,
    unknowns: list[Unknown],
    seen: set[tuple[str, str, str, str]],
) -> None:
    for index, startup in enumerate(profile.startupHistory):
        data = startup.model_dump(mode="python")
        funding = data.get("funding", {})
        if not isinstance(funding, Mapping) or _is_empty(funding.get("raised")):
            entity_id = str(data.get("id") or f"startup-{index + 1}")
            _add_unknown(
                unknowns,
                seen,
                category="missing_funding",
                field=f"startupHistory[{index}].funding.raised",
                reason="No funding amount is recorded for the startup.",
                priority="Medium",
                recommended_action=(
                    "Search financing announcements, filings, and investor databases."
                ),
                entity_type="startup",
                entity_id=entity_id,
            )


def _inspect_technical_background(
    profile: FounderProfile,
    unknowns: list[Unknown],
    seen: set[tuple[str, str, str, str]],
) -> None:
    skills = profile.skills.model_dump(mode="python")
    has_skills = any(values for values in skills.values() if isinstance(values, list))
    has_experience_skills = any(item.skillsUsed for item in profile.experience)
    has_project_technologies = any(item.technologies for item in profile.projects)
    has_repository_languages = any(
        item.primaryLanguage or item.languages for item in profile.repositories
    )
    if not any(
        (has_skills, has_experience_skills, has_project_technologies, has_repository_languages)
    ):
        _add_unknown(
            unknowns,
            seen,
            category="missing_technical_background",
            field="skills",
            reason=(
                "No structured technical skills, technologies, or programming languages "
                "are recorded."
            ),
            priority="Medium",
            recommended_action=(
                "Review the resume, repositories, project records, and technical publications."
            ),
        )


def _inspect_repositories(
    profile: FounderProfile,
    unknowns: list[Unknown],
    seen: set[tuple[str, str, str, str]],
) -> None:
    if not profile.repositories and profile.opensource.totalRepositories == 0:
        _add_unknown(
            unknowns,
            seen,
            category="missing_repositories",
            field="repositories",
            reason="No repositories or open-source repository count is recorded.",
            priority="Medium",
            recommended_action=(
                "Search GitHub and other code-hosting platforms for public repositories."
            ),
        )


def _inspect_timeline(
    profile: FounderProfile,
    unknowns: list[Unknown],
    seen: set[tuple[str, str, str, str]],
) -> None:
    for index, event in enumerate(profile.timeline):
        if not event.date:
            _add_unknown(
                unknowns,
                seen,
                category="incomplete_timeline",
                field=f"timeline[{index}].date",
                reason="A timeline event is present without a date.",
                priority="Medium",
                recommended_action=(
                    "Find the publication, announcement, or source date for this event."
                ),
                entity_type="timeline",
                entity_id=event.id or f"timeline-{index + 1}",
            )


def _inspect_verifications(
    source: VerificationInput,
    unknowns: list[Unknown],
    seen: set[tuple[str, str, str, str]],
) -> None:
    for item in _verification_items(source):
        claim_id = item.claimId
        strength = item.verification.supportStrength
        if strength == "Weak":
            _add_unknown(
                unknowns,
                seen,
                category="weakly_supported_fact",
                field=f"claim:{claim_id}",
                reason="The claim has only weak evidence support.",
                priority="Medium",
                recommended_action="Collect an independent source that states the claim directly.",
            )
        elif strength == NOT_MENTIONED:
            _add_unknown(
                unknowns,
                seen,
                category="unverified_claim",
                field=f"claim:{claim_id}",
                reason="The linked evidence does not mention the claim.",
                priority="High",
                recommended_action="Locate source text that explicitly addresses the claim.",
            )


def _verification_items(source: VerificationInput) -> list[ClaimVerification]:
    if source is None:
        return []
    if isinstance(source, ClaimVerification):
        raw_items: Iterable[ClaimVerification | Mapping[str, Any]] = [source]
    elif isinstance(source, Mapping):
        raw_items = source.get("verifications", [source])
    else:
        raw_items = source
    return [ClaimVerification.model_validate(item) for item in raw_items]


def _add_unknown(
    unknowns: list[Unknown],
    seen: set[tuple[str, str, str, str]],
    *,
    category: str,
    field: str,
    reason: str,
    priority: str,
    recommended_action: str,
    entity_type: str = "",
    entity_id: str = "",
) -> None:
    key = (category, field, entity_type, entity_id)
    if key in seen:
        return
    seen.add(key)
    unknowns.append(
        Unknown(
            category=category,
            field=field,
            reason=reason,
            importance=priority,
            priority=priority,
            recommendedAction=recommended_action,
            entityType=entity_type,
            entityId=entity_id,
        )
    )


def _priority_from_importance(importance: str) -> str:
    normalized = importance.casefold()
    if normalized in {"critical", "high"}:
        return "High"
    if normalized == "low":
        return "Low"
    return "Medium"


def _is_empty(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}