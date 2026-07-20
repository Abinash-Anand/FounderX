import asyncio
from types import SimpleNamespace

import pytest

from app.intelligence.search_planner import SearchPlanner, SearchPlanningError


class FakePlannerClient:
    def __init__(self, content: str) -> None:
        self.content = content
        self.calls = []

        completions = SimpleNamespace(create=self.create)
        self.chat = SimpleNamespace(completions=completions)

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.content))]
        )


def test_search_planner_returns_focused_searches() -> None:
    client = FakePlannerClient(
        '{"searches":["AI infrastructure startups Europe",'
        '"AI infrastructure startup founders Europe",'
        '"AI infrastructure startup funding Europe"]}'
    )

    plan = asyncio.run(SearchPlanner(client).plan("Find European AI infrastructure founders"))

    assert plan.searches == [
        "AI infrastructure startups Europe",
        "AI infrastructure startup founders Europe",
        "AI infrastructure startup funding Europe",
    ]
    assert client.calls[0]["response_format"]["type"] == "json_schema"
    assert "Each search should answer one question" in client.calls[0]["messages"][0]["content"]


def test_search_planner_rejects_invalid_output() -> None:
    client = FakePlannerClient('{"searches": []}')

    with pytest.raises(SearchPlanningError, match="invalid plan"):
        asyncio.run(SearchPlanner(client).plan("Find founders"))
