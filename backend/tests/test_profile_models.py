from app.intelligence.profile_models import FounderProfile, Layer1Input


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