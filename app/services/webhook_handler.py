"""Webhook handler — parses and routes incoming messages from all platforms."""

import logging
import json
from app.schemas.webhook import extract_platform, extract_sender_id, extract_message_text
from app.services.lead_service import get_or_create_lead, update_lead_from_ai
from app.services.claude_service import generate_response
from app.services.meta_service import send_text_message
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
        platform = extract_platform(payload)
        if not platform:
            logger.warning("Unknown platform in webhook payload")
            return

        sender_id = extract_sender_id(payload, platform)
        message_text = extract_message_text(payload, platform)

        if not sender_id or not message_text:
            logger.debug(f"Ignoring non-text message or status update on {platform}")
            return

        logger.info(f"Processing message from {platform}: sender={sender_id}")

        async with async_session() as session:
            # Get or create lead
            lead = await get_or_create_lead(session, platform, sender_id)

            # Get or create conversation
            conversation = await _get_or_create_conversation(session, lead.id, platform)

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

            # Load property data
            property_data = await load_properties()

            # Generate AI response
            ai_result = await generate_response(conversation_history, property_data)
            bot_reply = ai_result.get("reply", "عذراً، حصل مشكلة تقنية. حاول تاني بعد شوية.")
            lead_data = ai_result.get("lead_data", {})

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

            # Send response to customer
            await send_text_message(platform, sender_id, bot_reply)

            # Update lead with AI-extracted data
            if lead_data:
                async with async_session() as update_session:
                    lead = await update_lead_from_ai(update_session, lead.id, lead_data)
                    await update_session.commit()

                    # Notify sales team for hot leads
                    if lead and lead.status == LeadStatus.HOT:
                        await notify_sales_team(lead)

    except Exception as e:
        logger.error(f"Error processing incoming message: {e}", exc_info=True)


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
