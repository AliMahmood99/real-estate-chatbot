"""Webhook handler — parses and routes incoming messages from all platforms."""

import logging
import json
import traceback
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


async def process_incoming_message(payload: dict) -> None:
    """Process incoming webhook payload from Meta platforms."""
    try:
        logger.info(f"[WEBHOOK] Raw payload keys: {list(payload.keys())}")
        logger.info(f"[WEBHOOK] Payload object: {payload.get('object')}")

        platform = extract_platform(payload)
        if not platform:
            logger.warning(f"[WEBHOOK] Unknown platform in webhook payload: {payload.get('object')}")
            return

        sender_id = extract_sender_id(payload, platform)
        message_text = extract_message_text(payload, platform)

        logger.info(f"[WEBHOOK] Platform={platform}, sender_id={sender_id}, message_text={message_text!r}")

        if not sender_id or not message_text:
            logger.info(f"[WEBHOOK] Ignoring non-text message or status update on {platform}")
            return

        logger.info(f"[WEBHOOK] Processing message from {platform}: sender={sender_id}, text={message_text[:50]!r}")

        async with async_session() as session:
            # Get or create lead
            logger.info("[WEBHOOK] Step 1: Getting or creating lead...")
            lead = await get_or_create_lead(session, platform, sender_id)
            logger.info(f"[WEBHOOK] Lead: {lead.id}")

            # Get or create conversation
            logger.info("[WEBHOOK] Step 2: Getting or creating conversation...")
            conversation = await _get_or_create_conversation(session, lead.id, platform)
            logger.info(f"[WEBHOOK] Conversation: {conversation.id}")

            # Save customer message
            logger.info("[WEBHOOK] Step 3: Saving customer message...")
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
            logger.info("[WEBHOOK] Step 4: Fetching conversation history...")
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

            logger.info(f"[WEBHOOK] History has {len(conversation_history)} messages")

            # Load property data
            logger.info("[WEBHOOK] Step 5: Loading property data...")
            property_data = await load_properties()
            logger.info(f"[WEBHOOK] Property data loaded: {len(property_data)} chars")

            # Generate AI response
            logger.info("[WEBHOOK] Step 6: Calling Claude API...")
            ai_result = await generate_response(conversation_history, property_data)
            bot_reply = ai_result.get("reply", "عذراً، حصل مشكلة تقنية. حاول تاني بعد شوية.")
            lead_data = ai_result.get("lead_data", {})

            # Clean up markdown for WhatsApp
            # WhatsApp uses *text* for bold, not **text**
            bot_reply = _clean_for_whatsapp(bot_reply)
            logger.info(f"[WEBHOOK] Claude response: {len(bot_reply)} chars")

            # Save bot message
            logger.info("[WEBHOOK] Step 7: Saving bot message...")
            bot_msg = Message(
                conversation_id=conversation.id,
                sender_type=SenderType.BOT,
                content=bot_reply,
                platform=platform,
            )
            session.add(bot_msg)
            conversation.message_count += 1

            await session.commit()
            logger.info("[WEBHOOK] Step 8: DB commit successful")

            # Send response to customer
            logger.info(f"[WEBHOOK] Step 9: Sending reply to {platform} recipient {sender_id}...")
            send_success = await send_text_message(platform, sender_id, bot_reply)
            logger.info(f"[WEBHOOK] Message sent: {send_success}")

            # Update lead with AI-extracted data
            if lead_data:
                logger.info(f"[WEBHOOK] Step 10: Updating lead with AI data: {lead_data}")
                async with async_session() as update_session:
                    lead = await update_lead_from_ai(update_session, lead.id, lead_data)
                    await update_session.commit()

                    # Notify sales team for hot leads
                    if lead and lead.status == LeadStatus.HOT:
                        await notify_sales_team(lead)

            logger.info("[WEBHOOK] Processing complete!")

    except Exception as e:
        logger.error(f"[WEBHOOK] ERROR processing incoming message: {e}")
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

    # Remove emoji-only lines that look like markdown decorators
    # Keep actual content lines

    return text.strip()
