from app.intelligence.normalization import normalize_founder_payload


def test_normalize_founder_payload_cleans_known_values_without_mutating_input() -> None:
    payload = {
        "github": {
            "name": "  Ada   Lovelace ",
            "email": "ADA@EXAMPLE.COM ",
            "skills": ["Python Programming", "TS", "python"],
            "website": "example.com/ada/?utm_source=github",
            "createdAt": "2026-07-19T10:00:00Z",
        },
        "resume": {"name": "Ada Lovelace", "skills": ["NodeJS", "TS"]},
        "metadata": {"founderId": "founder-1"},
    }

    result = normalize_founder_payload(payload)

    assert payload["github"]["name"] == "  Ada   Lovelace "
    assert result["github"]["name"] == "Ada Lovelace"
    assert result["github"]["email"] == "ada@example.com"
    assert result["github"]["skills"] == ["Python", "TypeScript"]
    assert result["resume"]["skills"] == ["Node.js", "TypeScript"]
    assert result["github"]["website"] == "https://example.com/ada"
    assert result["github"]["createdAt"] == "2026-07-19T10:00:00+00:00"
    assert result["normalization"]["conflicts"] == []


def test_normalize_founder_payload_preserves_conflicting_source_values() -> None:
    result = normalize_founder_payload(
        {
            "github": {"name": "Ada Lovelace", "location": "London"},
            "website": {"name": "Ada Lovelace", "location": "New York"},
        }
    )

    assert result["github"]["location"] == "London"
    assert result["website"]["location"] == "New York"
    assert result["normalization"]["conflicts"] == [
        {
            "field": "founder.location",
            "values": [
                {"source": "github", "value": "London"},
                {"source": "website", "value": "New York"},
            ],
            "resolution": "preserved_for_entity_resolution",
        }
    ]