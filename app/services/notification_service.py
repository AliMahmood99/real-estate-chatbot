"""Sales team notification service."""

import logging
from app.models.lead import Lead
from app.config import get_settings
from app.services.meta_service import send_text_message

logger = logging.getLogger(__name__)
settings = get_settings()


async def notify_sales_team(lead: Lead) -> None:
    """
    Notify sales team about a hot lead via WhatsApp.

    Args:
        lead: Lead instance to notify about
    """
    try:
        # Check if sales team WhatsApp number is configured
        if not settings.SALES_TEAM_WHATSAPP:
            logger.info(f"No sales team WhatsApp configured, skipping notification for lead {lead.id}")
            return

        # Format notification message
        message = _format_notification_message(lead)

        logger.info(f"Sending hot lead notification for lead {lead.id} to sales team")

        # Send WhatsApp message to sales team
        success = await send_text_message(
            platform="whatsapp",
            recipient_id=settings.SALES_TEAM_WHATSAPP,
            text=message
        )

        if success:
            logger.info(f"Sales team notified successfully about lead {lead.id}")
        else:
            logger.warning(f"Failed to notify sales team about lead {lead.id}")

    except Exception as e:
        # Notification failure should NOT block the main flow
        logger.error(f"Error notifying sales team about lead {lead.id}: {e}", exc_info=True)


def _format_notification_message(lead: Lead) -> str:
    """
    Format notification message for sales team.

    Args:
        lead: Lead instance

    Returns:
        Formatted message string
    """
    # Emoji for hot lead
    message_parts = ["🔥 عميل Hot جديد — ركاز كومباوند!"]

    # Add name if available
    if lead.name:
        message_parts.append(f"الاسم: {lead.name}")
    else:
        message_parts.append("الاسم: غير متوفر")

    # Add phone if available
    if lead.phone:
        message_parts.append(f"التليفون: {lead.phone}")
    else:
        message_parts.append("التليفون: غير متوفر")

    # Add interested projects
    if lead.interested_projects and len(lead.interested_projects) > 0:
        projects = "، ".join(lead.interested_projects)
        message_parts.append(f"مهتم بـ: {projects}")

    # Add budget if available
    if lead.budget_range:
        message_parts.append(f"الميزانية: {lead.budget_range}")

    # Add timeline if available
    if lead.timeline:
        message_parts.append(f"التوقيت: {lead.timeline}")

    # Add platform
    platform_names = {
        "whatsapp": "واتساب",
        "messenger": "ماسنجر",
        "instagram": "إنستجرام"
    }
    platform_ar = platform_names.get(lead.platform.value, lead.platform.value)
    message_parts.append(f"المنصة: {platform_ar}")

    # Add lead ID for reference
    message_parts.append(f"\nرقم العميل: {lead.id}")

    return "\n".join(message_parts)
