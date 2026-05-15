"""
Lodge-Link API Entry Point
--------------------------
Read CLAUDE.md and docs/Lodge-Link_Implementation_Plan.md before modifying.
Every architectural decision in this file has a documented rationale.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import settings

# Initialize FastAPI with redirect_slashes=False to prevent CORS header stripping on redirects.
app = FastAPI(
    title="Lodge-Link API",
    description="B2B Hotel Referral Switch Middleware — Ethiopian Hospitality Sector",
    version="0.1.0",
    docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/api/redoc" if settings.ENVIRONMENT != "production" else None,
    redirect_slashes=False,
)

# CORSMiddleware must be initialized IMMEDIATELY after app and BEFORE any routers.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Router imports — all Phase 1 routes registered here.
# ---------------------------------------------------------------------------
from app.api.v1.auth import router as auth_router
from app.api.v1.availability import router as availability_router
from app.api.v1.handshake import router as handshake_router
from app.api.v1.referrals import router as referrals_router


@app.get("/", tags=["System"])
async def root():
    return {"message": "Lodge-Link API is running. Visit /health for status."}


@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "ok", "service": "lodge-link-api", "version": "0.1.0"}


@app.get("/status", tags=["System"])
async def status_check():
    """Full dependency health check — pings PostgreSQL and Redis."""
    from sqlalchemy.ext.asyncio import create_async_engine
    from redis.asyncio import Redis

    result = {"status": "ok", "version": "0.1.0", "database": "unknown", "cache": "unknown"}

    # DB ping
    try:
        engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        result["database"] = "ok"
        await engine.dispose()
    except Exception as e:
        result["database"] = f"error: {str(e)[:80]}"
        result["status"] = "degraded"

    # Redis ping
    try:
        redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        await redis.ping()
        result["cache"] = "ok"
        await redis.aclose()
    except Exception as e:
        result["cache"] = f"error: {str(e)[:80]}"
        result["status"] = "degraded"

    return result

# Register routers AFTER middleware
app.include_router(
    auth_router,
    prefix="/v1/auth",
    tags=["Authentication"],
)

app.include_router(
    availability_router,
    prefix="/v1/hotels",
    tags=["Availability"],
)

app.include_router(
    handshake_router,
    prefix="/v1/handshake",
    tags=["Handshake"],
)

app.include_router(
    referrals_router,
    prefix="/v1/referrals",
    tags=["Referrals"],
)
