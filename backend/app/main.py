from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.core.config import settings

# Initialize FastAPI with redirect_slashes=False to prevent header stripping
app = FastAPI(
    title="Lodge-Link API",
    version="0.1.0",
    redirect_slashes=False
)

# GLOBAL CATCH-ALL CORS (Must be the FIRST middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Router imports
from app.api.v1.auth import router as auth_router
from app.api.v1.availability import router as availability_router
from app.api.v1.handshake import router as handshake_router
from app.api.v1.referrals import router as referrals_router

@app.get("/")
async def root():
    return {"message": "Lodge-Link API is running"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Include routers AFTER middleware
app.include_router(auth_router, prefix="/v1/auth", tags=["Authentication"])
app.include_router(availability_router, prefix="/v1/hotels", tags=["Availability"])
app.include_router(handshake_router, prefix="/v1/handshake", tags=["Handshake"])
app.include_router(referrals_router, prefix="/v1/referrals", tags=["Referrals"])

@app.get("/status")
async def status_check():
    from sqlalchemy.ext.asyncio import create_async_engine
    from redis.asyncio import Redis
    result = {"status": "ok", "database": "unknown", "cache": "unknown"}
    try:
        engine = create_async_engine(settings.DATABASE_URL)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        result["database"] = "ok"
        await engine.dispose()
    except Exception as e:
        result["database"] = str(e)
    try:
        redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        await redis.ping()
        result["cache"] = "ok"
        await redis.aclose()
    except Exception as e:
        result["cache"] = str(e)
    return result
