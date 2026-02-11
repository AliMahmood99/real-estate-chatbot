"""Webhook router for receiving messages from WhatsApp, Messenger, and Instagram."""

import logging
from fastapi import APIRouter, BackgroundTasks, Request, Response, Query
from app.config import get_settings
from app.services.webhook_handler import process_incoming_message

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(tags=["webhook"])


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
) -> Response:
    """Meta webhook verification endpoint."""
    if hub_mode == "subscribe" and hub_verify_token == settings.META_VERIFY_TOKEN:
        logger.info("Webhook verification successful")
        return Response(content=hub_challenge, media_type="text/plain")
    logger.warning(f"Webhook verification failed: mode={hub_mode}")
    return Response(content="Verification failed", status_code=403)


@router.post("/webhook")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks) -> dict:
    """Receive webhook from Meta platforms. Returns 200 immediately, processes in background."""
    payload = await request.json()
    logger.info(f"Webhook received: object={payload.get('object')}")
    background_tasks.add_task(process_incoming_message, payload)
    return {"status": "ok"}
