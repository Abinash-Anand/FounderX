"""Deterministic normalization for Layer 2 founder-source payloads.

This module intentionally preserves source data instead of selecting a winner when
sources disagree. Entity merging and profile generation belong to later Layer 2
stages.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any, cast
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

_NODE_JS = "Node.js"
_TECHNOLOGY_ALIASES = {
    "ai": "AI",
    "amazon web services": "AWS",
    "aws": "AWS",
    "c sharp": "C#",
    "c#": "C#",
    "gcp": "Google Cloud",
    "google cloud platform": "Google Cloud",
    "js": "JavaScript",
    "nextjs": "Next.js",
    "next js": "Next.js",
    "node": _NODE_JS,
    "nodejs": _NODE_JS,
    "node js": _NODE_JS,
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "py": "Python",
    "python programming": "Python",
    "reactjs": "React",
    "react js": "React",
    "ts": "TypeScript",
    "typescript": "TypeScript",
}

_TECHNOLOGY_KEYS = {
    "aiml",
    "cloud",
    "databases",
    "devops",
    "frameworks",
    "languages",
    "primarylanguage",
    "programminglanguages",
    "skills",
    "skillsused",
    "technologies",
    "technology",
    "topics",
}
_DATE_KEYS = {
    "createdat",
    "date",
    "enddate",
    "generatedat",
    "lastupdated",
    "launchdate",
    "publishedat",
    "retrievedat",
    "startdate",
    "updatedat",
    "year",
}
_EMAIL_KEYS = {"email"}
_URL_KEYS = {
    "demourl",
    "github",
    "githubrepo",
    "googlescholar",
    "linkedin",
    "producthunt",
    "twitter",
    "url",
    "video",
    "website",
}
_BOOLEAN_KEYS = {"iscurrent", "isfork"}
_TRACKING_QUERY_PREFIXES = ("utm_",)
_TRACKING_QUERY_KEYS = {"fbclid", "gclid"}


def normalize_founder_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return a cleaned Layer 1 payload without mutating the caller's data.

    Values are normalized only when their key gives deterministic meaning. Empty
    strings become ``None``, lists are deduplicated in their original order, and
    source disagreements are reported under ``normalization.conflicts``. The
    original sources remain intact for later evidence-aware resolution.
    """
    normalized = _normalize_value(deepcopy(dict(payload)), key=None)
    conflicts = _find_founder_conflicts(normalized)
    metadata = normalized.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}
        normalized["metadata"] = metadata
    metadata = cast(dict[str, Any], metadata)

    existing_normalization = normalized.get("normalization")
    if not isinstance(existing_normalization, dict):
        existing_normalization = {}
        normalized["normalization"] = existing_normalization
    existing_normalization = cast(dict[str, Any], existing_normalization)
    existing_normalization.update(
        {
            "version": "1.0.0",
            "normalizedAt": datetime.now(UTC).isoformat(),
            "conflicts": conflicts,
        }
    )
    return normalized


def _normalize_value(value: Any, key: str | None) -> Any:
    normalized_key = _normalized_key(key)
    if isinstance(value, Mapping):
        mapping = cast(Mapping[str, Any], value)
        return {
            str(child_key): _normalize_value(child_value, str(child_key))
            for child_key, child_value in mapping.items()
        }
    if isinstance(value, list):
        items = [_normalize_value(item, key) for item in cast(list[Any], value)]
        return _deduplicate(items)
    if isinstance(value, str):
        text = " ".join(value.split())
        if not text:
            return None
        if normalized_key in _EMAIL_KEYS:
            return text.lower()
        if normalized_key in _URL_KEYS:
            return _normalize_url(text)
        if normalized_key in _DATE_KEYS:
            return _normalize_date(text)
        if normalized_key in _TECHNOLOGY_KEYS:
            return _TECHNOLOGY_ALIASES.get(text.casefold(), text)
        if normalized_key in _BOOLEAN_KEYS:
            return _normalize_boolean(text)
        return text
    return value


def _normalized_key(key: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", (key or "").casefold())


def _normalize_url(value: str) -> str:
    candidate = value if "://" in value else f"https://{value}"
    parts = urlsplit(candidate)
    if not parts.netloc:
        return value
    filtered_query = [
        (name, item)
        for name, item in parse_qsl(parts.query, keep_blank_values=True)
        if name.casefold() not in _TRACKING_QUERY_KEYS
        and not name.casefold().startswith(_TRACKING_QUERY_PREFIXES)
    ]
    return urlunsplit(
        (
            parts.scheme.casefold(),
            parts.netloc.casefold(),
            parts.path.rstrip("/"),
            urlencode(filtered_query),
            "",
        )
    )


def _normalize_date(value: str) -> str:
    """Normalize unambiguous ISO-like dates while retaining ambiguous input."""
    if re.fullmatch(r"\d{4}", value):
        return value
    if re.fullmatch(r"\d{4}-\d{2}", value):
        return value
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return value
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat()
    except ValueError:
        return value


def _normalize_boolean(value: str) -> bool | str:
    normalized = value.casefold()
    if normalized in {"true", "yes", "1", "current"}:
        return True
    if normalized in {"false", "no", "0", "former"}:
        return False
    return value


def _deduplicate(items: list[Any]) -> list[Any]:
    deduplicated: list[Any] = []
    fingerprints: set[str] = set()
    for item in items:
        fingerprint = item.casefold() if isinstance(item, str) else repr(item)
        if fingerprint not in fingerprints:
            fingerprints.add(fingerprint)
            deduplicated.append(item)
    return deduplicated


def _find_founder_conflicts(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Report conflicting scalar founder fields across Layer 1 source objects."""
    candidates: dict[str, list[dict[str, str]]] = {}
    for source_name in ("github", "resume", "website", "tavily"):
        source = payload.get(source_name)
        if not isinstance(source, Mapping):
            continue
        source_mapping = cast(Mapping[str, Any], source)
        founder = source_mapping.get("founder", source_mapping)
        if not isinstance(founder, Mapping):
            continue
        founder_mapping = cast(Mapping[str, Any], founder)
        for field in ("name", "email", "location", "website", "linkedin", "twitter"):
            value = founder_mapping.get(field)
            if isinstance(value, str) and value:
                candidates.setdefault(field, []).append({"source": source_name, "value": value})

    conflicts: list[dict[str, Any]] = []
    for field, values in candidates.items():
        distinct = {entry["value"].casefold() for entry in values}
        if len(distinct) > 1:
            conflicts.append(
                {
                    "field": f"founder.{field}",
                    "values": values,
                    "resolution": "preserved_for_entity_resolution",
                }
            )
    return conflicts