import asyncio
from types import SimpleNamespace

import pytest

from app.intelligence.founder_extraction import (
    FounderExtractionError,
    FounderIntelligenceExtractionAgent,
)


class FakeExtractionClient:
    def __init__(self, content: str) -> None:
        self.content = content
        self.calls = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.content))]
        )


def test_founder_extraction_returns_nullable_structured_data() -> None:
    client = FakeExtractionClient(
        '{"founders":[{"founderName":"Ada Lovelace","startup":"Analytical Engines",'
        '"startupWebsite":null,"startupDescription":"Computing company",'
        '"industry":"software","location":null,"funding":null,'
        '"employeeEstimate":null,"previousCompanies":null,"previousStartups":null,'
        '"previousExits":null,"technicalBackground":"Mathematics",'
        '"education":["University of London"],"researchPapers":null,'
        '"conferenceTalks":null,"awards":null,"socialLinks":null,'
        '"sources":[{"title":"Biography","url":"https://example.com/ada",'
        '"source":"example.com","supports":["founderName"]}]}]}'
    )

    result = asyncio.run(
        FounderIntelligenceExtractionAgent(client).extract(
            [{"title": "Biography", "url": "https://example.com/ada"}]
        )
    )

    assert result.founders[0].founderName == "Ada Lovelace"
    assert result.founders[0].startupWebsite is None
    assert result.founders[0].sources is not None
    assert result.founders[0].sources[0].url == "https://example.com/ada"
    assert client.calls[0]["response_format"]["json_schema"]["strict"] is True


def test_founder_extraction_requires_search_results() -> None:
    with pytest.raises(FounderExtractionError, match="search result"):
        asyncio.run(FounderIntelligenceExtractionAgent(FakeExtractionClient("{}")).extract([]))


def test_founder_extraction_maps_supported_claims_to_matching_sources() -> None:
    client = FakeExtractionClient(
        '{"founders":[{"founderName":"Ada Lovelace","startup":"Analytical Engines",'
        '"sources":[{"title":"Biography","url":"https://example.com/ada",'
        '"source":"example.com","supports":null}]}]}'
    )

    result = asyncio.run(
        FounderIntelligenceExtractionAgent(client).extract(
            [
                {
                    "title": "Biography",
                    "url": "https://example.com/ada",
                    "content": "Ada Lovelace founded Analytical Engines.",
                }
            ]
        )
    )

    assert result.founders[0].sources is not None
    assert result.founders[0].sources[0].supports == ["founderName", "startup"]
