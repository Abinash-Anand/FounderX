from fastapi import APIRouter

from app.api.routes import decisions, founders, health, media, research

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(decisions.router, prefix="/v1/decisions", tags=["decisions"])
api_router.include_router(founders.router, prefix="/v1/founders", tags=["founders"])
api_router.include_router(media.router, prefix="/v1/memos", tags=["media"])
api_router.include_router(research.router, prefix="/v1/research", tags=["research"])

