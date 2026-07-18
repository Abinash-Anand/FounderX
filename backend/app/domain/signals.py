from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class SignalKind(StrEnum):
    TRACTION = "traction"
    FOUNDER = "founder"
    MARKET = "market"
    COMPETITIVE = "competitive"
    RISK = "risk"


class SignalCreate(BaseModel):
    founder_id: UUID
    memo_id: UUID | None = None
    kind: SignalKind
    source_url: HttpUrl | None = None
    summary: str = Field(min_length=1)
    confidence: float = Field(default=0.5, ge=0, le=1)
    observed_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Signal(SignalCreate):
    id: UUID
    created_at: datetime

