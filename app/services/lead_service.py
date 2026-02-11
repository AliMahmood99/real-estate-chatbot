"""Lead service for CRUD operations and lead management."""

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.lead import Lead, LeadStatus, Platform

logger = logging.getLogger(__name__)


async def get_or_create_lead(
    session: AsyncSession,
    platform: str,
    sender_id: str
) -> Lead:
    """
    Get existing lead by platform and sender_id, or create a new one.

    Args:
        session: Async database session
        platform: Platform name ("whatsapp", "messenger", or "instagram")
        sender_id: Platform-specific sender ID

    Returns:
        Lead instance (existing or newly created)
    """
    # Convert platform string to enum
    platform_enum = Platform(platform)

    # Try to find existing lead
    result = await session.execute(
        select(Lead).where(
            and_(
                Lead.platform == platform_enum,
                Lead.platform_sender_id == sender_id
            )
        )
    )
    lead = result.scalar_one_or_none()

    if lead:
        # Update last_message_at
        lead.last_message_at = datetime.now(timezone.utc)
        logger.info(f"Found existing lead: {lead.id}")
        return lead

    # Create new lead
    lead = Lead(
        platform=platform_enum,
        platform_sender_id=sender_id,
        status=LeadStatus.NEW,
        last_message_at=datetime.now(timezone.utc)
    )
    session.add(lead)
    await session.flush()

    logger.info(f"Created new lead: {lead.id} on {platform}")
    return lead


async def update_lead_from_ai(
    session: AsyncSession,
    lead_id: UUID,
    extracted_data: dict[str, Any]
) -> Lead | None:
    """
    Update lead with data extracted by AI.
    Only updates fields that are present and not null in extracted_data.

    Args:
        session: Async database session
        lead_id: Lead UUID
        extracted_data: Dictionary with extracted lead data

    Returns:
        Updated Lead instance or None if not found
    """
    result = await session.execute(
        select(Lead).where(Lead.id == lead_id)
    )
    lead = result.scalar_one_or_none()

    if not lead:
        logger.warning(f"Lead not found: {lead_id}")
        return None

    # Track if any updates were made
    updated = False

    # Update name
    if "name" in extracted_data and extracted_data["name"]:
        if lead.name != extracted_data["name"]:
            lead.name = extracted_data["name"]
            updated = True
            logger.info(f"Updated lead {lead_id} name: {lead.name}")

    # Update phone
    if "phone" in extracted_data and extracted_data["phone"]:
        if lead.phone != extracted_data["phone"]:
            lead.phone = extracted_data["phone"]
            updated = True
            logger.info(f"Updated lead {lead_id} phone: {lead.phone}")

    # Update interested_project
    if "interested_project" in extracted_data and extracted_data["interested_project"]:
        project = extracted_data["interested_project"]
        # Add to interested_projects list if not already there
        if not lead.interested_projects:
            lead.interested_projects = []
        if project not in lead.interested_projects:
            lead.interested_projects.append(project)
            updated = True
            logger.info(f"Updated lead {lead_id} interested_projects: {lead.interested_projects}")

    # Update budget
    if "budget" in extracted_data and extracted_data["budget"]:
        if lead.budget_range != extracted_data["budget"]:
            lead.budget_range = extracted_data["budget"]
            updated = True
            logger.info(f"Updated lead {lead_id} budget: {lead.budget_range}")

    # Update timeline
    if "timeline" in extracted_data and extracted_data["timeline"]:
        if lead.timeline != extracted_data["timeline"]:
            lead.timeline = extracted_data["timeline"]
            updated = True
            logger.info(f"Updated lead {lead_id} timeline: {lead.timeline}")

    # Update preferred_type
    if "preferred_type" in extracted_data and extracted_data["preferred_type"]:
        if lead.preferred_type != extracted_data["preferred_type"]:
            lead.preferred_type = extracted_data["preferred_type"]
            updated = True
            logger.info(f"Updated lead {lead_id} preferred_type: {lead.preferred_type}")

    # Update preferred_size
    if "preferred_size" in extracted_data and extracted_data["preferred_size"]:
        if lead.preferred_size != extracted_data["preferred_size"]:
            lead.preferred_size = extracted_data["preferred_size"]
            updated = True
            logger.info(f"Updated lead {lead_id} preferred_size: {lead.preferred_size}")

    # Update payment_plan
    if "payment_plan" in extracted_data and extracted_data["payment_plan"]:
        if lead.payment_plan != extracted_data["payment_plan"]:
            lead.payment_plan = extracted_data["payment_plan"]
            updated = True
            logger.info(f"Updated lead {lead_id} payment_plan: {lead.payment_plan}")

    # Update classification/status
    if "classification" in extracted_data and extracted_data["classification"]:
        classification = extracted_data["classification"].lower()
        new_status = _map_classification_to_status(classification)

        # Only update status if it's different and not converted/lost
        if new_status and lead.status not in [LeadStatus.CONVERTED, LeadStatus.LOST]:
            if lead.status != new_status:
                lead.status = new_status
                updated = True
                logger.info(f"Updated lead {lead_id} status: {lead.status.value}")

    if updated:
        await session.flush()
        logger.info(f"Lead {lead_id} updated successfully")

    return lead


async def classify_lead(
    session: AsyncSession,
    lead_id: UUID,
    classification: str
) -> Lead | None:
    """
    Update lead status based on classification.

    Args:
        session: Async database session
        lead_id: Lead UUID
        classification: Classification string ("hot", "warm", "cold", "converted", "lost")

    Returns:
        Updated Lead instance or None if not found
    """
    result = await session.execute(
        select(Lead).where(Lead.id == lead_id)
    )
    lead = result.scalar_one_or_none()

    if not lead:
        logger.warning(f"Lead not found: {lead_id}")
        return None

    new_status = _map_classification_to_status(classification)
    if new_status and lead.status != new_status:
        lead.status = new_status
        await session.flush()
        logger.info(f"Lead {lead_id} classified as: {lead.status.value}")

    return lead


async def get_lead_by_id(
    session: AsyncSession,
    lead_id: UUID
) -> Lead | None:
    """
    Get lead by ID.

    Args:
        session: Async database session
        lead_id: Lead UUID

    Returns:
        Lead instance or None if not found
    """
    result = await session.execute(
        select(Lead).where(Lead.id == lead_id)
    )
    return result.scalar_one_or_none()


def _map_classification_to_status(classification: str) -> LeadStatus | None:
    """
    Map classification string to LeadStatus enum.

    Args:
        classification: Classification string

    Returns:
        LeadStatus enum or None if invalid
    """
    classification = classification.lower().strip()

    mapping = {
        "hot": LeadStatus.HOT,
        "warm": LeadStatus.WARM,
        "cold": LeadStatus.COLD,
        "converted": LeadStatus.CONVERTED,
        "lost": LeadStatus.LOST,
        "new": LeadStatus.NEW,
    }

    return mapping.get(classification)
