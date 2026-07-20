import asyncio
import json
from types import SimpleNamespace
from typing import Any

import pytest

from app.intelligence.research_agent import ResearchAgentError, VCResearchAgent
from app.intelligence.search_planner import SearchPlan


class FakeCompletions:
    def __init__(self, responses: list[Any]) -> None:
        self.responses = responses
        self.calls: list[dict[str, Any]] = []

    async def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        return self.responses.pop(0)


class FakeOpenAI:
    def __init__(self, responses: list[Any]) -> None:
        self.completions = FakeCompletions(responses)
        self.chat = SimpleNamespace(completions=self.completions)


class FakeTavily:
    def __init__(self) -> None:
        self.queries: list[str] = []

    def search(self, query: str, *, max_results: int = 5) -> dict[str, Any]:
        self.queries.append(query)
        return {
            "answer": f"Evidence for {query}",
            "results": [{"title": query, "url": f"https://example.com/{len(self.queries)}"}],
        }


def tool_response(query: str, call_id: str) -> Any:
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content=None,
                    tool_calls=[
                        SimpleNamespace(
                            id=call_id,
                            function=SimpleNamespace(
                                name="tavily_search",
                                arguments=json.dumps({"query": query, "max_results": 2}),
                            ),
                        )
                    ],
                )
            )
        ]
    )


def final_response() -> Any:
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content=json.dumps(
                        {
                            "tavily": {"claims": [{"founder": "Ada Lovelace"}]},
                            "metadata": {"dataSources": ["tavily"]},
                        }
                    ),
                    tool_calls=None,
                )
            )
        ]
    )


def test_research_agent_can_run_multiple_tavily_searches() -> None:
    openai = FakeOpenAI(
        [
            tool_response("AI infrastructure startup founders", "call-1"),
            tool_response("Ada Lovelace startup founder evidence", "call-2"),
            final_response(),
        ]
    )
    tavily = FakeTavily()
    agent = VCResearchAgent(openai, tavily)

    result = asyncio.run(agent.research("Find AI infrastructure founders"))

    assert tavily.queries == [
        "AI infrastructure startup founders",
        "Ada Lovelace startup founder evidence",
    ]
    assert result.tavily["claims"] == [{"founder": "Ada Lovelace"}]
    assert len(result.tavily["searches"]) == 2
    assert result.metadata.dataSources == ["tavily"]
    assert len(openai.completions.calls) == 3
    assert any(message["role"] == "tool" for message in openai.completions.calls[1]["messages"])


def test_research_agent_rejects_non_json_final_output() -> None:
    openai = FakeOpenAI(
        [
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content="not json", tool_calls=None)
                    )
                ]
            )
        ]
    )

    with pytest.raises(ResearchAgentError, match="did not match Layer1Input"):
        asyncio.run(VCResearchAgent(openai, FakeTavily()).research("Find founders"))


def test_research_agent_executes_planned_searches_before_final_reasoning() -> None:
    class FakePlanner:
        async def plan(self, query: str) -> SearchPlan:
            assert query == "Find AI infrastructure founders"
            return SearchPlan(
                searches=[
                    "AI infrastructure startups",
                    "AI infrastructure startup founders",
                ]
            )

    openai = FakeOpenAI([final_response()])
    tavily = FakeTavily()
    agent = VCResearchAgent(openai, tavily, planner=FakePlanner())

    result = asyncio.run(agent.research("Find AI infrastructure founders"))

    assert tavily.queries == [
        "AI infrastructure startups",
        "AI infrastructure startup founders",
    ]
    assert len(result.tavily["searches"]) == 2
    assert "initialTavilyResults" in openai.completions.calls[0]["messages"][2]["content"]
