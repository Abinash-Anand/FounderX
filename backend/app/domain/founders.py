from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, HttpUrl


class FounderCreate(BaseModel):
    user_id: UUID | None = None
    full_name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    company_name: str = Field(min_length=1, max_length=200)
    linkedin_url: HttpUrl | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Founder(FounderCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime

