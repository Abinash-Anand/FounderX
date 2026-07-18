from fastapi import APIRouter

from app.api.routes import decisions, health, media

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(decisions.router, prefix="/v1/decisions", tags=["decisions"])
api_router.include_router(media.router, prefix="/v1/memos", tags=["media"])

