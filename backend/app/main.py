import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request

from app.api.router import api_router
from app.core.settings import get_settings

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title="VC Brain Intelligence API",
        version="0.1.0",
        description="Stateful venture sourcing, diligence, decision, and media workflows.",
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.middleware("http")
    async def log_cors_preflight(request: Request, call_next):
        response = await call_next(request)
        if request.method == "OPTIONS":
            logger.info(
                "CORS preflight: origin=%s requested_method=%s configured_origins=%s "
                "status=%s allow_origin=%s",
                request.headers.get("origin"),
                request.headers.get("access-control-request-method"),
                settings.cors_origins,
                response.status_code,
                response.headers.get("access-control-allow-origin"),
            )
        return response

    application.include_router(api_router)
    return application


app = create_app()

