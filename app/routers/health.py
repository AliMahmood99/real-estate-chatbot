"""Health check endpoint."""

import logging
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter
from sqlalchemy import text

from app.config import get_settings
from app.database import engine

logger = logging.getLogger(__name__)
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


@router.get("/health/diagnose")
async def diagnose() -> dict:
    """Full diagnostic check: DB, Claude API, WhatsApp API."""
    settings = get_settings()
    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "db": "unknown",
        "claude_api": "unknown",
        "whatsapp_api": "unknown",
    }

    # 1. Test DB connection
    try:
        async with engine.begin() as conn:
            row = await conn.execute(text("SELECT COUNT(*) FROM leads"))
            count = row.scalar()
            results["db"] = f"ok (leads: {count})"
    except Exception as e:
        results["db"] = f"FAILED: {str(e)[:200]}"

    # 2. Test Claude API (just validate key, don't generate)
    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        msg = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=10,
            messages=[{"role": "user", "content": "hi"}],
        )
        results["claude_api"] = f"ok (model: {msg.model})"
    except Exception as e:
        results["claude_api"] = f"FAILED: {str(e)[:200]}"

    # 3. Test WhatsApp API (check token validity without sending)
    try:
        phone_id = settings.WHATSAPP_PHONE_NUMBER_ID
        token = settings.WHATSAPP_ACCESS_TOKEN
        url = f"https://graph.facebook.com/v21.0/{phone_id}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers={"Authorization": f"Bearer {token}"})
            if resp.status_code == 200:
                data = resp.json()
                results["whatsapp_api"] = f"ok (phone: {data.get('display_phone_number', 'N/A')})"
            else:
                results["whatsapp_api"] = f"FAILED: status={resp.status_code}, body={resp.text[:200]}"
    except Exception as e:
        results["whatsapp_api"] = f"FAILED: {str(e)[:200]}"

    return results
