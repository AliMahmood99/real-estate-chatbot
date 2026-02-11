"""Webhook handler — parses and routes incoming messages from all platforms."""

import asyncio
import logging
import json
import traceback
from datetime import datetime, timezone
from app.schemas.webhook import extract_platform, extract_sender_id, extract_message_text
from app.services.lead_service import get_or_create_lead, update_lead_from_ai
from app.services.claude_service import generate_response
from app.services.meta_service import send_text_message, send_whatsapp_list
from app.services.knowledge import load_properties
from app.services.notification_service import notify_sales_team
from app.database import async_session
from app.models.conversation import Conversation, Message, SenderType
from app.models.lead import LeadStatus
from sqlalchemy import select, desc, and_

logger = logging.getLogger(__name__)

# Debounce: collect rapid messages before responding
# Key: "platform:sender_id" → asyncio.Task that will process after delay
_pending_tasks: dict[str, asyncio.Task] = {}
# Buffer: store messages that arrived during debounce window
_message_buffer: dict[str, list[str]] = {}
# Lock to prevent race conditions on the buffer
_buffer_lock = asyncio.Lock()

DEBOUNCE_SECONDS = 3  # Wait 3 seconds to collect rapid messages


async def process_incoming_message(payload: dict) -> None:
    """Process incoming webhook payload from Meta platforms with debounce."""
    try:
        platform = extract_platform(payload)
        if not platform:
            logger.warning(f"[WEBHOOK] Unknown platform: {payload.get('object')}")
            return

        sender_id = extract_sender_id(payload, platform)
        message_text = extract_message_text(payload, platform)

        if not sender_id or not message_text:
            logger.info(f"[WEBHOOK] Ignoring non-text message on {platform}")
            return

        logger.info(f"[WEBHOOK] Message from {platform}/{sender_id}: {message_text[:50]!r}")

        # Debounce: buffer messages and reset timer
        buffer_key = f"{platform}:{sender_id}"

        async with _buffer_lock:
            # Add message to buffer
            if buffer_key not in _message_buffer:
                _message_buffer[buffer_key] = []
            _message_buffer[buffer_key].append(message_text)

            # Cancel existing pending task if any (reset timer)
            if buffer_key in _pending_tasks:
                _pending_tasks[buffer_key].cancel()
                logger.info(f"[DEBOUNCE] Reset timer for {buffer_key}, buffer now has {len(_message_buffer[buffer_key])} messages")

            # Schedule processing after debounce delay
            task = asyncio.create_task(
                _debounced_process(buffer_key, platform, sender_id)
            )
            _pending_tasks[buffer_key] = task

    except Exception as e:
        logger.error(f"[WEBHOOK] ERROR in debounce: {e}")
        logger.error(f"[WEBHOOK] Traceback: {traceback.format_exc()}")


async def _debounced_process(buffer_key: str, platform: str, sender_id: str) -> None:
    """Wait for debounce window, then process all buffered messages at once."""
    try:
        # Wait for debounce period
        await asyncio.sleep(DEBOUNCE_SECONDS)

        # Grab all buffered messages and clear
        async with _buffer_lock:
            messages_list = _message_buffer.pop(buffer_key, [])
            _pending_tasks.pop(buffer_key, None)

        if not messages_list:
            return

        # Combine all messages into one
        if len(messages_list) == 1:
            combined_text = messages_list[0]
        else:
            combined_text = "\n".join(messages_list)
            logger.info(f"[DEBOUNCE] Combined {len(messages_list)} messages for {buffer_key}: {combined_text[:80]!r}")

        # Process the combined message
        await _process_message(platform, sender_id, combined_text)

    except asyncio.CancelledError:
        # Timer was reset by a new message — this is expected
        logger.info(f"[DEBOUNCE] Timer cancelled for {buffer_key} (new message arrived)")
    except Exception as e:
        logger.error(f"[DEBOUNCE] ERROR processing {buffer_key}: {e}")
        logger.error(f"[DEBOUNCE] Traceback: {traceback.format_exc()}")


async def _process_message(platform: str, sender_id: str, message_text: str) -> None:
    """Process a single (possibly combined) message and generate AI response."""
    try:
        async with async_session() as session:
            # Get or create lead
            lead = await get_or_create_lead(session, platform, sender_id)
            logger.info(f"[WEBHOOK] Lead: {lead.id}")

            # Get or create conversation
            conversation = await _get_or_create_conversation(session, lead.id, platform)
            logger.info(f"[WEBHOOK] Conversation: {conversation.id}")

            # Save customer message
            customer_msg = Message(
                conversation_id=conversation.id,
                sender_type=SenderType.CUSTOMER,
                content=message_text,
                platform=platform,
            )
            session.add(customer_msg)
            conversation.message_count += 1
            await session.flush()

            # Get conversation history (last 20 messages)
            result = await session.execute(
                select(Message)
                .where(Message.conversation_id == conversation.id)
                .order_by(desc(Message.timestamp))
                .limit(20)
            )
            messages = list(reversed(result.scalars().all()))

            # Build conversation history for Claude
            conversation_history = []
            for msg in messages:
                role = "user" if msg.sender_type == SenderType.CUSTOMER else "assistant"
                conversation_history.append({"role": role, "content": msg.content})

            logger.info(f"[WEBHOOK] History: {len(conversation_history)} messages")

            # Load property data
            property_data = await load_properties()

            # Generate AI response
            logger.info("[WEBHOOK] Calling Claude API...")
            ai_result = await generate_response(conversation_history, property_data)
            bot_reply = ai_result.get("reply", "عذراً، حصل مشكلة تقنية. حاول تاني بعد شوية.")
            lead_data = ai_result.get("lead_data", {})

            # Clean up markdown for WhatsApp
            bot_reply = _clean_for_whatsapp(bot_reply)
            logger.info(f"[WEBHOOK] Claude response: {len(bot_reply)} chars")

            # Save bot message
            bot_msg = Message(
                conversation_id=conversation.id,
                sender_type=SenderType.BOT,
                content=bot_reply,
                platform=platform,
            )
            session.add(bot_msg)
            conversation.message_count += 1

            await session.commit()
            logger.info("[WEBHOOK] DB commit successful")

            # Send response to customer
            send_success = await send_text_message(platform, sender_id, bot_reply)
            logger.info(f"[WEBHOOK] Message sent: {send_success}")

            # Update lead with AI-extracted data
            if lead_data:
                logger.info(f"[WEBHOOK] Updating lead with AI data: {lead_data}")
                async with async_session() as update_session:
                    lead = await update_lead_from_ai(update_session, lead.id, lead_data)
                    await update_session.commit()

                    if lead and lead.status == LeadStatus.HOT:
                        await notify_sales_team(lead)

            logger.info("[WEBHOOK] Processing complete!")

    except Exception as e:
        logger.error(f"[WEBHOOK] ERROR processing message: {e}")
        logger.error(f"[WEBHOOK] Traceback: {traceback.format_exc()}")


async def _get_or_create_conversation(session, lead_id, platform) -> Conversation:
    """Get existing conversation or create a new one."""
    result = await session.execute(
        select(Conversation).where(
            and_(
                Conversation.lead_id == lead_id,
                Conversation.platform == platform,
            )
        ).order_by(desc(Conversation.last_message_at)).limit(1)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        conversation = Conversation(
            lead_id=lead_id,
            platform=platform,
            message_count=0,
        )
        session.add(conversation)
        await session.flush()

    return conversation


def _clean_for_whatsapp(text: str) -> str:
    """
    Clean Claude's markdown output for WhatsApp formatting.

    WhatsApp supports:
      *bold*  _italic_  ~strikethrough~  ```monospace```
    But NOT **bold** or other markdown syntax.
    """
    import re

    # Convert **bold** to *bold* (WhatsApp bold)
    text = re.sub(r'\*\*(.+?)\*\*', r'*\1*', text)

    # Remove ### headers — just keep the text
    text = re.sub(r'#{1,3}\s*', '', text)

    return text.strip()
