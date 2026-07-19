"""Canonicalize founder-profile evidence into a single immutable registry."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from app.intelligence.profile_models import Evidence


def normalize_evidence_registry_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return a profile payload with one registry and ID-only entity references."""
    result = deepcopy(dict(payload))
    evidence_records: list[dict[str, Any]] = []
    records_by_key: dict[str, dict[str, Any]] = {}
    aliases_by_raw_id: dict[str, str] = {}

    _collect_evidence_records(result, evidence_records)
    for raw_record in evidence_records:
        evidence = Evidence.model_validate(raw_record)
        evidence_data = evidence.model_dump(mode="python")
        identity_data = evidence.model_dump(mode="python", exclude={"id"})
        identity_key = _identity_key(identity_data)
        existing = records_by_key.setdefault(
            identity_key,
            {"evidence": identity_data, "raw_ids": set()},
        )
        raw_id = str(evidence_data.get("id", "")).strip()
        if raw_id:
            mapped_key = aliases_by_raw_id.get(raw_id)
            if mapped_key is not None and mapped_key != identity_key:
                raise ValueError(f"Evidence ID {raw_id!r} identifies conflicting evidence.")
            aliases_by_raw_id[raw_id] = identity_key
            existing["raw_ids"].add(raw_id)

    canonical_ids: dict[str, str] = {}
    keys_by_canonical_id: dict[str, str] = {}
    for identity_key, record in records_by_key.items():
        raw_ids = sorted(record["raw_ids"])
        canonical_id = raw_ids[0] if raw_ids else _generated_id(identity_key)
        previous_key = keys_by_canonical_id.get(canonical_id)
        if previous_key is not None and previous_key != identity_key:
            raise ValueError(f"Evidence ID {canonical_id!r} is not unique.")
        keys_by_canonical_id[canonical_id] = identity_key
        canonical_ids[identity_key] = canonical_id

    for raw_id, identity_key in list(aliases_by_raw_id.items()):
        aliases_by_raw_id[raw_id] = canonical_ids[identity_key]
    aliases_by_raw_id.update({value: value for value in canonical_ids.values()})

    _rewrite_entity_references(
        result,
        aliases_by_raw_id=aliases_by_raw_id,
        canonical_ids=canonical_ids,
    )
    result["evidence"] = [
        {**record["evidence"], "id": canonical_ids[identity_key]}
        for identity_key, record in records_by_key.items()
    ]
    return result


def register_evidence(profile: Any) -> Any:
    """Build a validated FounderProfile with canonical evidence references."""
    from app.intelligence.profile_models import FounderProfile

    if isinstance(profile, FounderProfile):
        return FounderProfile.model_validate(profile.model_dump(mode="python"))
    if not isinstance(profile, Mapping):
        return FounderProfile.model_validate(profile)
    return FounderProfile.model_validate(normalize_evidence_registry_payload(profile))


def validate_evidence_references(profile_data: Mapping[str, Any]) -> None:
    """Reject profiles whose entity references do not exist in the registry."""
    registry = profile_data.get("evidence", [])
    if not isinstance(registry, list):
        return
    evidence_ids = {
        item.get("id")
        for item in registry
        if isinstance(item, Mapping) and isinstance(item.get("id"), str)
    }
    _validate_reference_nodes(profile_data, evidence_ids)


def _collect_evidence_records(node: Any, records: list[dict[str, Any]]) -> None:
    if isinstance(node, Mapping):
        for key, value in node.items():
            if key == "evidence" and isinstance(value, list):
                records.extend(item for item in value if isinstance(item, Mapping))
            elif key != "evidence":
                _collect_evidence_records(value, records)
    elif isinstance(node, list):
        for item in node:
            _collect_evidence_records(item, records)


def _rewrite_entity_references(
    node: Any,
    *,
    aliases_by_raw_id: Mapping[str, str],
    canonical_ids: Mapping[str, str],
    is_root: bool = True,
) -> None:
    if isinstance(node, dict):
        _rewrite_entity_dict(
            node,
            aliases_by_raw_id=aliases_by_raw_id,
            canonical_ids=canonical_ids,
            is_root=is_root,
        )
    elif isinstance(node, list):
        _rewrite_entity_list(
            node,
            aliases_by_raw_id=aliases_by_raw_id,
            canonical_ids=canonical_ids,
        )


def _rewrite_entity_dict(
    node: dict[str, Any],
    *,
    aliases_by_raw_id: Mapping[str, str],
    canonical_ids: Mapping[str, str],
    is_root: bool,
) -> None:
    embedded_evidence = node.pop("evidence", None) if not is_root else None
    if isinstance(embedded_evidence, list):
        embedded_ids = [
            canonical_ids[
                _identity_key(
                    Evidence.model_validate(item).model_dump(
                        mode="python", exclude={"id"}
                    )
                )
            ]
            for item in embedded_evidence
            if isinstance(item, Mapping)
        ]
        node["evidenceIds"] = _merge_ids(
            node.get("evidenceIds", []),
            embedded_ids,
            aliases_by_raw_id,
        )
    elif "evidenceIds" in node:
        node["evidenceIds"] = _merge_ids(node["evidenceIds"], [], aliases_by_raw_id)
    for value in node.values():
        _rewrite_entity_references(
            value,
            aliases_by_raw_id=aliases_by_raw_id,
            canonical_ids=canonical_ids,
            is_root=False,
        )


def _rewrite_entity_list(
    node: list[Any],
    *,
    aliases_by_raw_id: Mapping[str, str],
    canonical_ids: Mapping[str, str],
) -> None:
    for item in node:
        _rewrite_entity_references(
            item,
            aliases_by_raw_id=aliases_by_raw_id,
            canonical_ids=canonical_ids,
            is_root=False,
        )


def _merge_ids(
    existing_ids: Any,
    additional_ids: list[str],
    aliases_by_raw_id: Mapping[str, str],
) -> list[str]:
    if not isinstance(existing_ids, list):
        raise ValueError("evidenceIds must be an array of evidence IDs.")
    merged: list[str] = []
    for evidence_id in [*existing_ids, *additional_ids]:
        if not isinstance(evidence_id, str) or not evidence_id.strip():
            raise ValueError("evidenceIds must contain non-empty strings.")
        canonical_id = aliases_by_raw_id.get(evidence_id)
        if canonical_id is None:
            raise ValueError(f"Evidence ID {evidence_id!r} is not present in evidence[].")
        if canonical_id not in merged:
            merged.append(canonical_id)
    return merged


def _validate_reference_nodes(node: Any, evidence_ids: set[str]) -> None:
    if isinstance(node, Mapping):
        references = node.get("evidenceIds")
        if isinstance(references, list):
            missing = [reference for reference in references if reference not in evidence_ids]
            if missing:
                raise ValueError(f"Unknown evidence IDs: {', '.join(missing)}")
        for value in node.values():
            _validate_reference_nodes(value, evidence_ids)
    elif isinstance(node, list):
        for item in node:
            _validate_reference_nodes(item, evidence_ids)


def _identity_key(identity_data: Mapping[str, Any]) -> str:
    return json.dumps(identity_data, sort_keys=True, separators=(",", ":"), default=str)


def _generated_id(identity_key: str) -> str:
    digest = hashlib.sha256(identity_key.encode("utf-8")).hexdigest()[:16]
    return f"evidence-{digest}"