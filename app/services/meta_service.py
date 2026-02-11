"""Meta API service for sending messages to WhatsApp, Messenger, and Instagram."""

import logging
import asyncio
from typing import Literal
import httpx
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Rate limiting and retry configuration
MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]  # Exponential backoff in seconds


async def send_text_message(
    platform: str,
    recipient_id: str,
    text: str
) -> bool:
    """
    Send a text message to a recipient on the specified platform.

    Args:
        platform: Platform name ("whatsapp", "messenger", or "instagram")
        recipient_id: Recipient's platform-specific ID
        text: Message text to send

    Returns:
        True if message sent successfully, False otherwise
    """
    logger.info(f"Sending message to {platform} recipient {recipient_id}")

    for attempt in range(MAX_RETRIES):
        try:
            if platform == "whatsapp":
                success = await _send_whatsapp_message(recipient_id, text)
            elif platform == "messenger":
                success = await _send_messenger_message(recipient_id, text)
            elif platform == "instagram":
                success = await _send_instagram_message(recipient_id, text)
            else:
                logger.error(f"Unknown platform: {platform}")
                return False

            if success:
                logger.info(f"Message sent successfully to {platform} recipient {recipient_id}")
                return True

            # If unsuccessful but no exception, don't retry
            return False

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                # Rate limit hit
                logger.warning(f"Rate limit hit on {platform} (attempt {attempt + 1}/{MAX_RETRIES})")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAYS[attempt])
                    continue
            else:
                logger.error(f"HTTP error sending message to {platform}: {e.response.status_code} - {e.response.text}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAYS[attempt])
                    continue

        except Exception as e:
            logger.error(f"Error sending message to {platform} (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(RETRY_DELAYS[attempt])
                continue

    logger.error(f"Failed to send message to {platform} after {MAX_RETRIES} attempts")
    return False


async def _send_whatsapp_message(recipient_id: str, text: str) -> bool:
    """Send message via WhatsApp Cloud API."""
    phone_id = settings.WHATSAPP_PHONE_NUMBER_ID
    access_token = settings.WHATSAPP_ACCESS_TOKEN

    if not phone_id:
        logger.error("[META] WHATSAPP_PHONE_NUMBER_ID is empty!")
        return False
    if not access_token:
        logger.error("[META] WHATSAPP_ACCESS_TOKEN is empty!")
        return False

    url = f"https://graph.facebook.com/v21.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_id,
        "type": "text",
        "text": {
            "body": text
        }
    }

    logger.info(f"[META] WhatsApp API request to {url}, recipient={recipient_id}, text_len={len(text)}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        logger.info(f"[META] WhatsApp API response status={response.status_code}")
        logger.info(f"[META] WhatsApp API response body={response.text}")
        response.raise_for_status()
        return True


async def _send_messenger_message(recipient_id: str, text: str) -> bool:
    """Send message via Messenger API."""
    # Send typing indicator first
    await _send_typing_indicator("messenger", recipient_id)

    url = f"https://graph.facebook.com/v21.0/me/messages"
    params = {
        "access_token": settings.MESSENGER_PAGE_ACCESS_TOKEN
    }
    payload = {
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": text
        }
    }

    logger.debug(f"Messenger API request to {url}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, params=params, json=payload)
        response.raise_for_status()
        logger.debug(f"Messenger API response: {response.json()}")
        return True


async def _send_instagram_message(recipient_id: str, text: str) -> bool:
    """Send message via Instagram API."""
    # Send typing indicator first
    await _send_typing_indicator("instagram", recipient_id)

    url = f"https://graph.facebook.com/v21.0/me/messages"
    params = {
        "access_token": settings.INSTAGRAM_ACCESS_TOKEN
    }
    payload = {
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": text
        }
    }

    logger.debug(f"Instagram API request to {url}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, params=params, json=payload)
        response.raise_for_status()
        logger.debug(f"Instagram API response: {response.json()}")
        return True


async def send_whatsapp_buttons(
    recipient_id: str,
    body_text: str,
    buttons: list[dict[str, str]],
) -> bool:
    """
    Send WhatsApp interactive reply buttons (max 3 buttons).

    Args:
        recipient_id: Recipient's phone number
        body_text: Main message text
        buttons: List of dicts with 'id' and 'title' keys (max 3)

    Returns:
        True if sent successfully
    """
    phone_id = settings.WHATSAPP_PHONE_NUMBER_ID
    access_token = settings.WHATSAPP_ACCESS_TOKEN

    if not phone_id or not access_token:
        logger.error("[META] WhatsApp credentials missing for buttons")
        return False

    url = f"https://graph.facebook.com/v21.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    # Build button rows (max 3)
    button_rows = []
    for btn in buttons[:3]:
        button_rows.append({
            "type": "reply",
            "reply": {
                "id": btn["id"],
                "title": btn["title"][:20]  # WhatsApp max 20 chars
            }
        })

    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_id,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body_text},
            "action": {"buttons": button_rows}
        }
    }

    logger.info(f"[META] Sending WhatsApp buttons to {recipient_id}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            logger.info(f"[META] WhatsApp buttons response: {response.status_code}")
            response.raise_for_status()
            return True
    except Exception as e:
        logger.error(f"[META] Failed to send WhatsApp buttons: {e}")
        return False


async def send_whatsapp_list(
    recipient_id: str,
    body_text: str,
    button_text: str,
    sections: list[dict],
) -> bool:
    """
    Send WhatsApp interactive list message (max 10 items).

    Args:
        recipient_id: Recipient's phone number
        body_text: Main message text
        button_text: Text on the list button (max 20 chars)
        sections: List of section dicts with 'title' and 'rows'

    Returns:
        True if sent successfully
    """
    phone_id = settings.WHATSAPP_PHONE_NUMBER_ID
    access_token = settings.WHATSAPP_ACCESS_TOKEN

    if not phone_id or not access_token:
        logger.error("[META] WhatsApp credentials missing for list")
        return False

    url = f"https://graph.facebook.com/v21.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_id,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": body_text},
            "action": {
                "button": button_text[:20],
                "sections": sections
            }
        }
    }

    logger.info(f"[META] Sending WhatsApp list to {recipient_id}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            logger.info(f"[META] WhatsApp list response: {response.status_code}")
            response.raise_for_status()
            return True
    except Exception as e:
        logger.error(f"[META] Failed to send WhatsApp list: {e}")
        return False


async def _send_typing_indicator(platform: Literal["messenger", "instagram"], recipient_id: str) -> None:
    """
    Send typing indicator for Messenger/Instagram.

    Args:
        platform: Either "messenger" or "instagram"
        recipient_id: Recipient's platform-specific ID
    """
    try:
        url = f"https://graph.facebook.com/v21.0/me/messages"

        if platform == "messenger":
            access_token = settings.MESSENGER_PAGE_ACCESS_TOKEN
        else:  # instagram
            access_token = settings.INSTAGRAM_ACCESS_TOKEN

        params = {
            "access_token": access_token
        }
        payload = {
            "recipient": {
                "id": recipient_id
            },
            "sender_action": "typing_on"
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(url, params=params, json=payload)
            logger.debug(f"Typing indicator sent to {platform} recipient {recipient_id}")

    except Exception as e:
        # Don't fail if typing indicator fails
        logger.warning(f"Failed to send typing indicator to {platform}: {e}")
