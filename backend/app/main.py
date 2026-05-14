"""
Lodge-Link API Entry Point
--------------------------
Read CLAUDE.md and docs/Lodge-Link_Implementation_Plan.md before modifying.
Every architectural decision in this file has a documented rationale.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

app = FastAPI(
    title="Lodge-Link API",
    description="B2B Hotel Referral Switch Middleware — Ethiopian Hospitality Sector",
    version="0.1.0",
    docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/api/redoc" if settings.ENVIRONMENT != "production" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.v1.availability import router as availability_router
from app.api.v1.handshake import router as handshake_router

@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "ok", "service": "lodge-link-api", "version": "0.1.0"}

app.include_router(
    availability_router,
    prefix="/v1/hotels",
    tags=["Availability"]
)

app.include_router(
    handshake_router,
    prefix="/v1/handshake",
    tags=["Handshake"]
)
