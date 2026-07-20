from typing import Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.core.errors import IntegrationNotConfigured

router = APIRouter()


@router.post("/pitch-deck")
async def upload_pitch_deck(file: Annotated[UploadFile, File()]) -> dict[str, str]:
    from uuid import uuid4

    from app.core.settings import get_settings
    from app.integrations.mongodb import build_mongodb_gateway

    settings = get_settings()
    if not file.filename:
        raise HTTPException(status_code=400, detail="A pitch deck filename is required.")

    content = await file.read()
    if len(content) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="That deck is larger than 25 MB.")

    path = f"{uuid4()}-{file.filename}"
    try:
        storage_path = build_mongodb_gateway(settings).upload_private_file(
            bucket=settings.mongodb_pitch_deck_bucket,
            path=path,
            content=content,
            content_type=file.content_type or "application/octet-stream",
        )
    except IntegrationNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return {"storage_path": storage_path}


class NarrateMemoRequest(BaseModel):
    text: str = Field(min_length=1, max_length=100_000)


class NarrateMemoResponse(BaseModel):
    storage_path: str


@router.post("/{memo_id}/audio", response_model=NarrateMemoResponse)
async def narrate_memo(memo_id: str, request: NarrateMemoRequest) -> NarrateMemoResponse:
    # Keep the ElevenLabs client off the startup path.
    from app.integrations.elevenlabs.memo_audio import build_memo_narrator

    try:
        narrator = build_memo_narrator()
        storage_path = await narrator.narrate_and_store(memo_id, request.text)
    except IntegrationNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return NarrateMemoResponse(storage_path=storage_path)

