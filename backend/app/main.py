"""
LeadGen & Competitor Intelligence Pipeline
FastAPI Application Entry Point
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.models import HealthResponse
from app.routers import leads, intelligence

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")

    # Test database connection on startup
    db_status = "disconnected"
    try:
        from app.database import get_supabase
        client = get_supabase()
        db_status = "connected"
        logger.info("Supabase connection established")
    except Exception as e:
        logger.warning(f"Supabase connection failed: {e}")
        logger.warning("API will start but database operations will fail")

    app.state.db_status = db_status

    yield

    logger.info("Shutting down application")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Pipeline de generare lead-uri și analiză competitivă. "
        "Identifică afaceri fără site web și extrage 'Formula Câștigătoare' "
        "de la competitorii lor de top."
    ),
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
origins = settings.cors_origins.split(",") if settings.cors_origins != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(leads.router)
app.include_router(intelligence.router)


# ============================================================================
# Root & Health Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "Pipeline de generare lead-uri și analiză competitivă",
        "docs": "/api/docs",
        "health": "/api/health",
    }


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for Railway monitoring."""
    db_status = getattr(app.state, "db_status", "unknown")

    # Re-check database if it was disconnected
    if db_status != "connected":
        try:
            from app.database import get_supabase
            get_supabase()
            db_status = "connected"
            app.state.db_status = db_status
        except Exception:
            db_status = "disconnected"

    return HealthResponse(
        status="ok",
        version=settings.app_version,
        database=db_status,
    )


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Resursa solicitată nu a fost găsită"},
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Eroare internă a serverului"},
    )
