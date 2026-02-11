"""Health check endpoint."""

from datetime import datetime, timezone

from fastapi import APIRouter
from app.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    """Check API health status."""
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
    }


@router.get("/health/config")
async def config_check() -> dict:
    """Check if critical environment variables are configured (no secrets shown)."""
    settings = get_settings()
    return {
        "ANTHROPIC_API_KEY": "set" if settings.ANTHROPIC_API_KEY else "MISSING",
        "WHATSAPP_ACCESS_TOKEN": "set" if settings.WHATSAPP_ACCESS_TOKEN else "MISSING",
        "WHATSAPP_PHONE_NUMBER_ID": settings.WHATSAPP_PHONE_NUMBER_ID or "MISSING",
        "META_VERIFY_TOKEN": "set" if settings.META_VERIFY_TOKEN else "MISSING",
        "DATABASE_URL": "set" if settings.DATABASE_URL else "MISSING",
        "APP_ENV": settings.APP_ENV,
        "LOG_LEVEL": settings.LOG_LEVEL,
    }
