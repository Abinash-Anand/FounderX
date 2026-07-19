"""Stable identifier propagation across founder intelligence pipeline layers."""

from __future__ import annotations

from uuid import NAMESPACE_URL, uuid4, uuid5

from app.intelligence.profile_models import FounderProfile, Layer1Input


def ensure_layer1_founder_identifier(
    payload: Layer1Input,
    fallback_id: str | None = None,
) -> Layer1Input:
    """Return a Layer 1 payload with a stable founder identifier."""

    founder_id = payload.metadata.founderId.strip() or fallback_id or str(uuid4())
    metadata = payload.metadata.model_copy(update={"founderId": founder_id})
    return payload.model_copy(update={"metadata": metadata})


def founder_identifier_for_query(query: str) -> str:
    """Return a repeatable UUID for repeated analysis of the same query."""

    normalized_query = " ".join(query.casefold().split())
    return str(uuid5(NAMESPACE_URL, f"foundex:founder:{normalized_query}"))


def ensure_founder_profile_identifiers(
    profile: FounderProfile,
    founder_id: str | None = None,
) -> FounderProfile:
    """Populate both profile identifiers with one stable value."""

    stable_id = (
        profile.founder.id.strip()
        or profile.metadata.profileId.strip()
        or (founder_id or "").strip()
        or str(uuid4())
    )
    founder = profile.founder.model_copy(update={"id": stable_id})
    metadata = profile.metadata.model_copy(update={"profileId": stable_id})
    return profile.model_copy(update={"founder": founder, "metadata": metadata})