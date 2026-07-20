"""Final memo and presentation artifacts generated after investment analysis."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class InvestmentMemoArtifact(BaseModel):
    """Generated final memo assets stored as an immutable versioned record."""

    model_config = ConfigDict(extra="forbid")

    memo: str
    executiveSummary: str
    narration: str = ""
    audioUrl: str = ""
    generatedCharts: list[dict[str, Any]] = Field(default_factory=list)
    presentationMetadata: dict[str, Any] = Field(default_factory=dict)