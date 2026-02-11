"""Webhook payload schemas and helper functions for WhatsApp, Messenger, and Instagram."""

from typing import Any, Literal
from pydantic import BaseModel


class WhatsAppMessage(BaseModel):
    """WhatsApp webhook message schema."""
    messaging_product: str
    from_: str
    text: dict[str, Any]


class MessengerMessage(BaseModel):
    """Messenger/Instagram webhook message schema."""
    sender: dict[str, str]
    message: dict[str, Any]
    is_echo: bool | None = None


def extract_platform(payload: dict) -> str | None:
    """
    Extract platform type from webhook payload.

    Args:
        payload: The webhook payload dictionary

    Returns:
        Platform name: "whatsapp", "messenger", or "instagram", or None if unknown
    """
    object_type = payload.get("object")

    if object_type == "whatsapp_business_account":
        return "whatsapp"
    elif object_type == "page":
        return "messenger"
    elif object_type == "instagram":
        return "instagram"

    return None


def extract_sender_id(payload: dict, platform: str) -> str | None:
    """
    Extract sender ID from webhook payload based on platform.

    Args:
        payload: The webhook payload dictionary
        platform: Platform name ("whatsapp", "messenger", or "instagram")

    Returns:
        Sender ID string or None if not found
    """
    try:
        if platform == "whatsapp":
            # WhatsApp: messages in entry[].changes[].value.messages[]
            entries = payload.get("entry", [])
            for entry in entries:
                changes = entry.get("changes", [])
                for change in changes:
                    value = change.get("value", {})
                    messages = value.get("messages", [])
                    if messages:
                        # Return first message sender
                        return messages[0].get("from")

        elif platform in ["messenger", "instagram"]:
            # Messenger/Instagram: messages in entry[].messaging[]
            entries = payload.get("entry", [])
            for entry in entries:
                messaging = entry.get("messaging", [])
                if messaging:
                    sender = messaging[0].get("sender", {})
                    return sender.get("id")

    except (KeyError, IndexError, AttributeError):
        return None

    return None


def extract_message_text(payload: dict, platform: str) -> str | None:
    """
    Extract message text from webhook payload based on platform.
    Filters out status updates and echo messages.

    Args:
        payload: The webhook payload dictionary
        platform: Platform name ("whatsapp", "messenger", or "instagram")

    Returns:
        Message text string or None if not found/not a text message
    """
    try:
        if platform == "whatsapp":
            # WhatsApp: messages in entry[].changes[].value.messages[]
            entries = payload.get("entry", [])
            for entry in entries:
                changes = entry.get("changes", [])
                for change in changes:
                    value = change.get("value", {})

                    # Skip status updates (delivery receipts, read receipts)
                    if value.get("statuses"):
                        return None

                    messages = value.get("messages", [])
                    if messages:
                        message = messages[0]
                        # Only process text messages
                        if message.get("type") == "text":
                            text_obj = message.get("text", {})
                            return text_obj.get("body")

        elif platform in ["messenger", "instagram"]:
            # Messenger/Instagram: messages in entry[].messaging[]
            entries = payload.get("entry", [])
            for entry in entries:
                messaging = entry.get("messaging", [])
                if messaging:
                    msg_event = messaging[0]

                    # Skip echo messages (messages sent by the bot)
                    if msg_event.get("message", {}).get("is_echo"):
                        return None

                    # Extract text from message
                    message = msg_event.get("message", {})
                    return message.get("text")

    except (KeyError, IndexError, AttributeError):
        return None

    return None
