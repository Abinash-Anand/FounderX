"""Layer 4 investment-intelligence output contract."""

from pydantic import BaseModel, ConfigDict, Field


class InvestmentIntelligence(BaseModel):
    """Investment assessment that enriches persisted founder intelligence."""

    model_config = ConfigDict(extra="forbid")

    founderScores: dict[str, float] = Field(default_factory=dict)
    categoryScores: dict[str, float] = Field(default_factory=dict)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    opportunities: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    recommendation: str = ""
    confidence: float = 0.0