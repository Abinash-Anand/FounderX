from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.errors import IntegrationNotConfigured

router = APIRouter()


class NarrateMemoRequest(BaseModel):
    text: str = Field(min_length=1, max_length=100_000)


class NarrateMemoResponse(BaseModel):
    storage_path: str


@router.post("/{memo_id}/audio", response_model=NarrateMemoResponse)
async def narrate_memo(memo_id: str, request: NarrateMemoRequest) -> NarrateMemoResponse:
    # ElevenLabs and Supabase clients are kept off the startup path.
    from app.integrations.elevenlabs.memo_audio import build_memo_narrator

    try:
        narrator = build_memo_narrator()
        storage_path = await narrator.narrate_and_store(memo_id, request.text)
    except IntegrationNotConfigured as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return NarrateMemoResponse(storage_path=storage_path)

