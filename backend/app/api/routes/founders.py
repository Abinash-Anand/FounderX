from fastapi import APIRouter, HTTPException

from app.core.settings import get_settings
from app.intelligence.llm_normalization import OpenAIProfileClient, structure_founder_profile
from app.intelligence.profile_models import FounderProfile, Layer1Input

router = APIRouter()


@router.post(
    "/structure",
    responses={503: {"description": "OpenAI structuring integration is not configured."}},
)
async def structure_founder(payload: Layer1Input) -> FounderProfile:
    settings = get_settings()
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=503,
            detail="Founder structuring requires OPENAI_API_KEY.",
        )
    api_key = settings.openai_api_key.get_secret_value() if settings.openai_api_key else ""
    client = OpenAIProfileClient(api_key=api_key)
    return await structure_founder_profile(payload, client)
