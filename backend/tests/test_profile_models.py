import pytest
from pydantic import ValidationError

from app.intelligence.contradiction_detection import detect_contradictions
from app.intelligence.entity_confidence import calculate_entity_confidence
from app.intelligence.evidence_classification import classify_evidence_registry
from app.intelligence.evidence_reliability import calculate_evidence_reliability
from app.intelligence.evidence_verification import verify_claim, verify_claims
from app.intelligence.profile_models import FounderProfile, Layer1Input
from app.intelligence.unknown_detection import detect_unknowns


def test_layer1_input_accepts_partial_collector_payload() -> None:
    payload = Layer1Input.model_validate(
        {
            "github": {"username": "ada", "repositories": []},
            "metadata": {"founderId": "founder-1", "collectedAt": "2026-07-19"},
        }
    )

    assert payload.github["username"] == "ada"
    assert payload.resume == {}
    assert payload.metadata.founderId == "founder-1"


def test_founder_profile_has_the_complete_empty_output_shape() -> None:
    profile = FounderProfile()
    output = profile.model_dump()

    assert output["metadata"]["schemaVersion"] == "1.0.0"
    assert output["founder"]["name"] == ""
    assert output["skills"]["programmingLanguages"] == []
    assert output["opensource"]["totalRepositories"] == 0
    assert output["unknowns"] == []


def test_founder_profile_rejects_unknown_output_fields() -> None:
    try:
        FounderProfile.model_validate({"unexpected": True})
    except ValueError as error:
        assert "unexpected" in str(error)
    else:
        raise AssertionError("FounderProfile accepted an unknown field")


def test_founder_profile_deduplicates_embedded_evidence_and_uses_ids() -> None:
    evidence = {
        "id": "source-1",
        "type": "article",
        "title": "Founder interview",
        "source": "Example News",
        "url": "https://example.com/interview",
        "retrievedAt": "2026-07-19",
        "publishedAt": "2026-07-18",
        "confidence": "high",
        "supports": ["founder.name"],
    }

    profile = FounderProfile.model_validate(
        {
            "education": [{"institution": "University", "evidence": [evidence]}],
            "experience": [{"company": "Example", "evidence": [dict(evidence)]}],
        }
    )

    output = profile.model_dump()
    assert len(output["evidence"]) == 1
    assert output["evidence"][0]["id"] == "source-1"
    assert output["education"][0]["evidenceIds"] == ["source-1"]
    assert output["experience"][0]["evidenceIds"] == ["source-1"]
    assert "evidence" not in output["education"][0]
    assert "evidence" not in output["experience"][0]
    assert _find_embedded_evidence(output) == []


def test_evidence_without_id_gets_a_stable_deterministic_id() -> None:
    evidence = {
        "type": "repository",
        "title": "Public repository",
        "url": "https://github.com/example/project",
    }

    first = FounderProfile.model_validate(
        {"projects": [{"name": "Project", "evidence": [evidence]}]}
    )
    second = FounderProfile.model_validate(
        {"projects": [{"name": "Project", "evidence": [dict(evidence)]}]}
    )

    first_id = first.evidence[0].id
    assert first_id.startswith("evidence-")
    assert first_id == second.evidence[0].id
    assert first.projects[0].evidenceIds == [first_id]


def test_existing_evidence_ids_are_checked_for_referential_integrity() -> None:
    with pytest.raises(ValueError, match="not present in evidence"):
        FounderProfile.model_validate(
            {"projects": [{"evidenceIds": ["missing-evidence"]}]}
        )


def test_evidence_objects_are_immutable() -> None:
    profile = FounderProfile.model_validate(
        {"evidence": [{"id": "source-1", "title": "Immutable source"}]}
    )

    with pytest.raises(ValidationError):
        profile.evidence[0].id = "source-2"


def test_evidence_classification_is_deterministic_and_preserves_references() -> None:
    profile = FounderProfile.model_validate(
        {
            "evidence": [
                {
                    "id": "github-1",
                    "type": "repository",
                    "title": "Founder project",
                    "url": "https://github.com/example/project",
                    "supports": ["technicalBackground"],
                },
                {
                    "id": "paper-1",
                    "type": "paper",
                    "title": "Research paper",
                    "url": "https://doi.org/10.1000/example",
                    "supports": ["researchPapers"],
                },
            ],
            "projects": [{"evidenceIds": ["github-1"]}],
        }
    )

    first = classify_evidence_registry(profile)
    second = classify_evidence_registry(profile)

    assert first.model_dump() == second.model_dump()
    assert first.projects[0].evidenceIds == ["github-1"]
    assert first.evidence[0].sourceCategory == "GitHub"
    assert first.evidence[0].publisherType == "code_host"
    assert first.evidence[0].contentType == "code_repository"
    assert first.evidence[0].claimCategory == "technical"
    assert first.evidence[1].sourceCategory == "Research Paper"
    assert first.evidence[1].contentType == "research_paper"
    assert first.evidence[1].claimCategory == "research"


def test_ambiguous_evidence_is_classified_as_unknown() -> None:
    profile = classify_evidence_registry(
        {"evidence": [{"id": "unknown-1", "url": "https://example.com"}]}
    )

    evidence = profile.evidence[0]
    assert evidence.sourceCategory == "Unknown"
    assert evidence.publisherType == "unknown"
    assert evidence.contentType == "Unknown"
    assert evidence.claimCategory == "Unknown"


def test_claim_verification_detects_direct_quoted_support() -> None:
    verification = verify_claim(
        {
            "id": "claim-1",
            "field": "founder.name",
            "value": "Ada Lovelace",
            "text": "Ada Lovelace founded Analytical Engines.",
            "evidenceIds": ["source-1"],
        },
        {
            "evidence": [
                {
                    "id": "source-1",
                    "sourceCategory": "Official Website",
                    "supports": ["founder.name"],
                    "quote": "Ada Lovelace founded Analytical Engines.",
                }
            ]
        },
    )

    assert verification.model_dump() == {
        "supportStrength": "Strong",
        "supportType": "Quoted",
        "reasoning": "The supplied evidence states the claim text verbatim.",
        "limitations": [],
    }


def test_claim_verification_detects_contradiction_without_scoring() -> None:
    verification = verify_claim(
        {
            "field": "founder.currentCompany",
            "value": "Example Labs",
            "evidenceIds": ["source-1"],
        },
        [
            {
                "id": "source-1",
                "sourceCategory": "News",
                "supports": ["founder.currentCompany"],
                "content": "The founder does not work at Example Labs.",
            }
        ],
    )

    assert verification.supportStrength == "Contradicted"
    assert verification.supportType == "Secondary"
    assert "negates" in verification.reasoning


def test_claim_verification_does_not_infer_support_from_missing_text() -> None:
    verification = verify_claim(
        {
            "field": "founder.name",
            "value": "Ada Lovelace",
            "evidenceIds": ["source-1"],
        },
        {"evidence": [{"id": "source-1", "supports": ["founder.name"]}]},
    )

    assert verification.supportStrength == "Not Mentioned"
    assert "No evidence content" in verification.limitations[0]


def test_claim_verifications_keep_claim_links_and_unknown_ids_explicit() -> None:
    results = verify_claims(
        [{"id": "claim-1", "evidenceIds": ["missing"]}],
        {"evidence": []},
    )

    assert len(results) == 1
    assert results[0].claimId == "claim-1"
    assert results[0].evidenceIds == ["missing"]
    assert results[0].verification.supportStrength == "Not Mentioned"
    assert "missing" in results[0].verification.limitations[0]


def test_evidence_reliability_is_deterministic_and_uses_configured_factors() -> None:
    registry = {
        "evidence": [
            {
                "id": "source-1",
                "source": "Company registry",
                "url": "https://example.gov/company",
                "publishedAt": "2026-07-19",
            },
            {
                "id": "source-2",
                "source": "Example News",
                "url": "https://news.example.com/story",
                "publishedAt": "2025-01-01",
            },
        ]
    }
    classification = {
        "evidence": [
            {"id": "source-1", "sourceCategory": "Government"},
            {"id": "source-2", "sourceCategory": "News"},
        ]
    }
    verification = [
        {
            "claimId": "claim-1",
            "evidenceIds": ["source-1", "source-2"],
            "verification": {
                "supportStrength": "Strong",
                "supportType": "Primary",
                "reasoning": "The supplied evidence states the claim.",
                "limitations": [],
            },
        }
    ]

    first = calculate_evidence_reliability(
        registry,
        classification,
        verification,
        as_of="2026-07-19",
    )
    second = calculate_evidence_reliability(
        registry,
        classification,
        verification,
        as_of="2026-07-19",
    )

    assert first == second
    assert [item.evidenceId for item in first] == ["source-1", "source-2"]
    assert first[0].reliability.factorBreakdown.sourceCredibility == 95.0
    assert first[0].reliability.factorBreakdown.directness == 100.0
    assert first[0].reliability.factorBreakdown.corroboration == 75.0
    assert first[0].reliability.overallScore > 0
    assert first[0].reliability.explanation


def test_evidence_reliability_scores_unverified_evidence_without_founder_scores() -> None:
    results = calculate_evidence_reliability(
        {"evidence": [{"id": "source-1", "sourceCategory": "Unknown"}]},
        evidence_verification=[],
        weights={
            "sourceCredibility": 1,
            "directness": 0,
            "corroboration": 0,
            "freshness": 0,
            "identityMatch": 0,
            "claimSpecificity": 0,
        },
    )

    reliability = results[0].reliability
    assert reliability.sourceReliability == 20.0
    assert reliability.claimReliability == 0.0
    assert reliability.overallEvidenceReliability == 20.0
    assert reliability.factorBreakdown.corroboration == 0.0
    assert "No linked verification" in reliability.explanation


def test_entity_confidence_aggregates_quality_and_tracks_evidence_extremes() -> None:
    profile = {
        "founder": {"id": "founder-1", "name": "Ada Lovelace"},
        "evidence": [
            {"id": "strong-1", "title": "First strong source"},
            {"id": "strong-2", "title": "Second strong source"},
            {"id": "weak-1", "title": "Weak source"},
        ],
        "education": [
            {
                "id": "education-1",
                "institution": "University",
                "evidenceIds": ["strong-1", "strong-2", "weak-1"],
            }
        ],
    }
    reliability = [
        _reliability_result("strong-1", 90),
        _reliability_result("strong-2", 90),
        _reliability_result("weak-1", 20),
    ]

    results = calculate_entity_confidence(profile, reliability)

    assert len(results) == 1
    education = results[0]
    assert education.entityType == "education"
    assert education.entityId == "education-1"
    assert education.supportingEvidence == ["strong-1", "strong-2", "weak-1"]
    assert education.strongestEvidence == "strong-1"
    assert education.weakestEvidence == "weak-1"
    assert education.confidence > 80
    assert education.coverage == 100.0
    assert education.confidenceBreakdown.corroboration == 100.0
    assert all(item.entityType != "founder" for item in results)


def test_entity_confidence_reports_coverage_and_empty_entity_support() -> None:
    profile = {
        "evidence": [
            {"id": "known", "title": "Known source"},
            {"id": "missing", "title": "Unscored source"},
        ],
        "experience": [{"company": "Example", "evidenceIds": ["known", "missing"]}],
        "projects": [{"id": "project-1", "name": "Project"}],
    }

    results = calculate_entity_confidence(
        profile,
        [_reliability_result("known", 80)],
    )

    experience, project = results
    assert experience.coverage == 50.0
    assert experience.supportingEvidence == ["known"]
    assert project.entityId == "project-1"
    assert project.confidence == 0.0
    assert project.supportingEvidence == []
    assert project.confidenceBreakdown.coverage == 0.0


def test_entity_confidence_is_deterministic_for_multiple_entity_types() -> None:
    profile = {
        "evidence": [{"id": "source-1"}],
        "startupHistory": [{"company": "Startup", "evidenceIds": ["source-1"]}],
        "projects": [{"name": "Project", "evidenceIds": ["source-1"]}],
        "patents": [{"title": "Patent", "evidenceIds": ["source-1"]}],
        "awards": [{"title": "Award", "evidenceIds": ["source-1"]}],
        "research": [{"title": "Publication", "evidenceIds": ["source-1"]}],
    }
    reliability = [_reliability_result("source-1", 75)]

    first = calculate_entity_confidence(profile, reliability)
    second = calculate_entity_confidence(profile, reliability)

    assert first == second
    assert [item.entityType for item in first] == [
        "startup",
        "project",
        "patent",
        "award",
        "publication",
    ]


def test_contradictions_cluster_values_and_preserve_all_evidence() -> None:
    claims = [
        {
            "id": "claim-1",
            "entityType": "startup",
            "entityId": "startup-1",
            "field": "foundingYear",
            "value": "2010",
            "evidenceIds": ["source-1"],
        },
        {
            "id": "claim-2",
            "entityType": "startup",
            "entityId": "startup-1",
            "field": "foundingYear",
            "value": "2012",
            "evidenceIds": ["source-2"],
        },
        {
            "id": "claim-3",
            "entityType": "startup",
            "entityId": "startup-1",
            "field": "foundingYear",
            "value": "2010",
            "evidenceIds": ["source-3"],
        },
    ]

    conflicts = detect_contradictions(claims)

    assert len(conflicts) == 1
    conflict = conflicts[0]
    assert conflict.entityType == "startup"
    assert conflict.entityId == "startup-1"
    assert conflict.field == "foundingYear"
    assert [value.value for value in conflict.values] == ["2010", "2012"]
    assert conflict.values[0].supportingEvidence == ["source-1", "source-3"]
    assert conflict.supportingEvidence == ["source-1", "source-3", "source-2"]
    assert conflict.severity == "High"
    assert conflict.review.required is True
    assert conflict.review.status == "needs_review"


def test_contradictions_scope_values_to_the_same_entity_and_normalize_duplicates() -> None:
    claims = [
        {
            "entityType": "experience",
            "entityId": "experience-1",
            "field": "company",
            "value": "Example Labs",
            "evidenceIds": ["source-1"],
        },
        {
            "entityType": "experience",
            "entityId": "experience-1",
            "field": "company",
            "value": " example   labs ",
            "evidenceIds": ["source-2"],
        },
        {
            "entityType": "experience",
            "entityId": "experience-2",
            "field": "company",
            "value": "Different Company",
            "evidenceIds": ["source-3"],
        },
    ]

    assert detect_contradictions(claims) == []


def test_contradictions_surface_low_severity_without_evidence_and_do_not_overwrite() -> None:
    claims = [
        {
            "id": "claim-1",
            "entityType": "award",
            "entityId": "award-1",
            "field": "title",
            "value": "Best Paper",
        },
        {
            "id": "claim-2",
            "entityType": "award",
            "entityId": "award-1",
            "field": "title",
            "value": "Top Paper",
        },
    ]

    conflicts = detect_contradictions(claims)

    assert len(conflicts) == 1
    assert [value.value for value in conflicts[0].values] == ["Best Paper", "Top Paper"]
    assert conflicts[0].supportingEvidence == []
    assert conflicts[0].severity == "Low"


def test_unknown_detection_reports_observable_profile_gaps() -> None:
    unknowns = detect_unknowns(FounderProfile())

    categories = {unknown.category for unknown in unknowns}
    assert "missing_evidence" in categories
    assert "missing_entity" in categories
    assert "missing_technical_background" in categories
    assert "missing_repositories" in categories
    assert unknowns
    assert all(unknown.reason for unknown in unknowns)
    assert all(unknown.priority for unknown in unknowns)
    assert all(unknown.recommendedAction for unknown in unknowns)


def test_unknown_detection_reports_entity_dates_funding_evidence_and_timeline_gaps() -> None:
    profile = FounderProfile.model_validate(
        {
            "evidence": [{"id": "source-1", "title": "Startup source"}],
            "startupHistory": [
                {"id": "startup-1", "company": "Example", "evidenceIds": ["source-1"]}
            ],
            "timeline": [{"id": "event-1", "title": "Launch"}],
            "projects": [{"id": "project-1", "name": "Project"}],
        }
    )

    unknowns = detect_unknowns(profile)
    fields = {unknown.field for unknown in unknowns}
    categories = {unknown.category for unknown in unknowns}

    assert "startupHistory[0].startDate" in fields
    assert "startupHistory[0].funding.raised" in fields
    assert "projects[0].evidenceIds" in fields
    assert "timeline[0].date" in fields
    assert "missing_funding" in categories
    assert "incomplete_timeline" in categories


def test_unknown_detection_reports_weak_and_unverified_claims_without_scoring() -> None:
    unknowns = detect_unknowns(
        FounderProfile(),
        [
            {
                "claimId": "claim-weak",
                "evidenceIds": ["source-1"],
                "verification": {
                    "supportStrength": "Weak",
                    "supportType": "Inferred",
                    "reasoning": "Terms overlap.",
                    "limitations": [],
                },
            },
            {
                "claimId": "claim-unknown",
                "evidenceIds": [],
                "verification": {
                    "supportStrength": "Not Mentioned",
                    "supportType": "Inferred",
                    "reasoning": "No text.",
                    "limitations": [],
                },
            },
        ],
    )

    claim_unknowns = [unknown for unknown in unknowns if unknown.field.startswith("claim:")]
    assert {unknown.category for unknown in claim_unknowns} == {
        "weakly_supported_fact",
        "unverified_claim",
    }
    assert all("score" not in unknown.reason.casefold() for unknown in claim_unknowns)


def test_unknown_detection_preserves_existing_unknowns_and_does_not_mutate_profile() -> None:
    profile = FounderProfile.model_validate(
        {
            "unknowns": [
                {
                    "field": "founder.linkedin",
                    "reason": "No LinkedIn profile was supplied.",
                    "importance": "high",
                    "recommendedAction": "Search professional networks.",
                }
            ]
        }
    )
    before = profile.model_dump()

    unknowns = detect_unknowns(profile)

    assert profile.model_dump() == before
    existing = next(unknown for unknown in unknowns if unknown.field == "founder.linkedin")
    assert existing.category == "existing_unknown"
    assert existing.priority == "High"
    assert existing.recommendedAction == "Search professional networks."


def _reliability_result(evidence_id: str, score: float) -> dict[str, object]:
    return {
        "evidenceId": evidence_id,
        "reliability": {
            "sourceReliability": score,
            "claimReliability": score,
            "overallEvidenceReliability": score,
            "overallScore": score,
            "factorBreakdown": {
                "sourceCredibility": score,
                "directness": score,
                "corroboration": score,
                "freshness": score,
                "identityMatch": score,
                "claimSpecificity": score,
            },
            "explanation": "Deterministic test reliability.",
        },
    }


def _find_embedded_evidence(value: object, path: str = "") -> list[str]:
    if isinstance(value, dict):
        found = [path] if "evidence" in value and path else []
        for key, child in value.items():
            found.extend(_find_embedded_evidence(child, f"{path}.{key}".strip(".")))
        return found
    if isinstance(value, list):
        found: list[str] = []
        for index, child in enumerate(value):
            found.extend(_find_embedded_evidence(child, f"{path}[{index}]"))
        return found
    return []