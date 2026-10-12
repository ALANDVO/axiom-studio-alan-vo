"""Axiom Studio FastAPI application entrypoint."""
from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator, Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.audit_routes import router as audit_router
from app.api.auth_routes import router as auth_router
from app.api.macro_routes import router as macro_router
from app.api.ml_routes import router as ml_router
from app.api.spatial_routes import router as spatial_router
from app.core.config import settings
from app.models.database import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("axiom.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: initialize database schemas and verify security constraints."""
    logger.info("Initializing Axiom Studio persistent database schemas...")
    init_db()
    settings.validate_production_safety()
    logger.info(
        "Axiom Studio started successfully (environment=%s, demo_mode=%s)",
        settings.environment,
        settings.demo_mode,
    )
    yield
    logger.info("Axiom Studio shutting down cleanly.")


def create_app() -> FastAPI:
    """Application factory for Axiom Studio."""
    application = FastAPI(
        title="Axiom Studio API",
        description="Live spatial intelligence simulator and ML trajectory anomaly evaluation platform.",
        version=settings.version,
        lifespan=lifespan,
    )

    # CORS configuration for frontend dev server
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:3000",
            "http://localhost:3000",
            "http://127.0.0.1:80",
            "http://localhost:80",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check endpoint
    @application.get("/api/health")
    def health_check() -> Dict[str, str]:
        return {
            "status": "healthy",
            "application": settings.app_name,
            "version": settings.version,
            "environment": settings.environment,
            "demo_mode": str(settings.demo_mode).lower(),
        }

    # Register API routers
    application.include_router(auth_router)
    application.include_router(spatial_router)
    application.include_router(ml_router)
    application.include_router(macro_router)
    application.include_router(audit_router)

    return application


app = create_app()
