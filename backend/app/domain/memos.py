from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class MemoStatus(StrEnum):
    DRAFT = "draft"
    SCREENING = "screening"
    DILIGENCE = "diligence"
    APPROVED = "approved"
    DECLINED = "declined"


class MemoCreate(BaseModel):
    founder_id: UUID
    title: str = Field(min_length=1, max_length=300)
    thesis: str = ""
    recommendation: str | None = None
    status: MemoStatus = MemoStatus.DRAFT
    score: float | None = Field(default=None, ge=0, le=100)


class Memo(MemoCreate):
    id: UUID
    audio_storage_path: str | None = None
    created_at: datetime
    updated_at: datetime

