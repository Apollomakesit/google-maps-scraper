"""
LeadGen & Competitor Intelligence Pipeline
FastAPI Application Entry Point

Designed for Railway deployment - crash-proof startup with lazy imports.
"""

import logging
import sys
import traceback

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# ============================================================================
# Step 1: Create a minimal FastAPI app that always starts
# (even if dependencies or config are broken)
# ============================================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

_startup_errors: list[str] = []

app = FastAPI(
    title="LeadGen Intelligence Pipeline",
    version="1.0.0",
    description="Pipeline de generare lead-uri și analiză competitivă.",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS - allow everything by default
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Step 2: Health endpoint (always available, even if nothing else works)
# ============================================================================

@app.get("/")
async def root():
    return {
        "name": "LeadGen Intelligence Pipeline",
        "version": "1.0.0",
        "status": "running",
        "docs": "/api/docs",
        "health": "/api/health",
        "startup_errors": _startup_errors if _startup_errors else None,
    }


@app.get("/api/health")
async def health_check():
    db_status = "unknown"
    try:
        from app.database import get_supabase
        get_supabase()
        db_status = "connected"
    except Exception as e:
        db_status = f"disconnected: {e}"

    return {
        "status": "ok",
        "version": "1.0.0",
        "database": db_status,
        "startup_errors": _startup_errors if _startup_errors else None,
    }


# ============================================================================
# Step 3: Try to load config and routers (non-fatal if they fail)
# ============================================================================

try:
    from app.config import settings
    logger.info(f"Config loaded: debug={settings.debug}, supabase_url={'SET' if settings.supabase_url else 'NOT SET'}")

    # Update CORS with configured origins
    if settings.cors_origins and settings.cors_origins != "*":
        origins = settings.cors_origins.split(",")
        logger.info(f"CORS origins: {origins}")
except Exception as e:
    err = f"Config load failed: {e}"
    logger.error(err)
    logger.error(traceback.format_exc())
    _startup_errors.append(err)

try:
    from app.routers import leads
    app.include_router(leads.router)
    logger.info("Leads router loaded")
except Exception as e:
    err = f"Leads router failed to load: {e}"
    logger.error(err)
    logger.error(traceback.format_exc())
    _startup_errors.append(err)

try:
    from app.routers import intelligence
    app.include_router(intelligence.router)
    logger.info("Intelligence router loaded")
except Exception as e:
    err = f"Intelligence router failed to load: {e}"
    logger.error(err)
    logger.error(traceback.format_exc())
    _startup_errors.append(err)


# ============================================================================
# Step 4: Try to connect to Supabase (non-fatal)
# ============================================================================

try:
    from app.database import get_supabase
    client = get_supabase()
    logger.info("Supabase connection established")
except Exception as e:
    logger.warning(f"Supabase connection failed (non-fatal): {e}")
    _startup_errors.append(f"Supabase: {e}")


# ============================================================================
# Error handlers
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


if _startup_errors:
    logger.warning(f"App started with {len(_startup_errors)} error(s): {_startup_errors}")
else:
    logger.info("App started successfully with all components loaded")
