"""Admin API router with API key authentication."""

import json
import logging
from datetime import datetime, timezone, timedelta
from uuid import UUID
from pathlib import Path
from math import ceil

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import select, func, and_, desc, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.lead import Lead, LeadStatus, Platform
from app.models.conversation import Conversation, Message
from app.schemas.admin import (
    DashboardStats,
    LeadResponse,
    LeadUpdateRequest,
    PaginatedResponse,
    ConversationResponse,
    MessageResponse,
)

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/api/admin", tags=["admin"])


async def verify_api_key(x_api_key: str = Header(...)) -> str:
    """Verify admin API key from header."""
    if x_api_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> DashboardStats:
    """Get dashboard statistics."""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)

    # Leads today
    result = await db.execute(
        select(func.count(Lead.id)).where(Lead.created_at >= today_start)
    )
    leads_today = result.scalar() or 0

    # Leads this week
    result = await db.execute(
        select(func.count(Lead.id)).where(Lead.created_at >= week_start)
    )
    leads_this_week = result.scalar() or 0

    # Leads this month
    result = await db.execute(
        select(func.count(Lead.id)).where(Lead.created_at >= month_start)
    )
    leads_this_month = result.scalar() or 0

    # Leads by platform
    result = await db.execute(
        select(Lead.platform, func.count(Lead.id))
        .group_by(Lead.platform)
    )
    leads_by_platform = {row[0].value: row[1] for row in result.fetchall()}

    # Leads by status
    result = await db.execute(
        select(Lead.status, func.count(Lead.id))
        .group_by(Lead.status)
    )
    leads_by_status = {row[0].value: row[1] for row in result.fetchall()}

    # Top projects (flatten interested_projects JSON arrays and count)
    result = await db.execute(
        select(Lead.interested_projects)
        .where(Lead.interested_projects.isnot(None))
    )
    project_counts: dict[str, int] = {}
    for row in result.fetchall():
        projects = row[0] or []
        for project in projects:
            if isinstance(project, str):
                project_counts[project] = project_counts.get(project, 0) + 1

    top_projects = [
        {"name": name, "count": count}
        for name, count in sorted(project_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    ]

    # Recent leads
    result = await db.execute(
        select(Lead)
        .order_by(desc(Lead.created_at))
        .limit(10)
    )
    leads = result.scalars().all()
    recent_leads = [
        {
            "id": str(lead.id),
            "name": lead.name,
            "phone": lead.phone,
            "platform": lead.platform.value,
            "status": lead.status.value,
            "created_at": lead.created_at.isoformat(),
        }
        for lead in leads
    ]

    return DashboardStats(
        leads_today=leads_today,
        leads_this_week=leads_this_week,
        leads_this_month=leads_this_month,
        leads_by_platform=leads_by_platform,
        leads_by_status=leads_by_status,
        top_projects=top_projects,
        recent_leads=recent_leads,
    )


@router.get("/leads", response_model=PaginatedResponse)
async def get_leads(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    platform: str | None = Query(None),
    status: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> PaginatedResponse:
    """Get paginated list of leads with optional filters."""
    # Build filters
    filters = []
    if platform:
        try:
            filters.append(Lead.platform == Platform(platform))
        except ValueError:
            pass
    if status:
        try:
            filters.append(Lead.status == LeadStatus(status))
        except ValueError:
            pass
    if date_from:
        try:
            date_from_dt = datetime.fromisoformat(date_from.replace("Z", "+00:00"))
            filters.append(Lead.created_at >= date_from_dt)
        except ValueError:
            pass
    if date_to:
        try:
            date_to_dt = datetime.fromisoformat(date_to.replace("Z", "+00:00"))
            filters.append(Lead.created_at <= date_to_dt)
        except ValueError:
            pass

    # Get total count
    count_query = select(func.count(Lead.id))
    if filters:
        count_query = count_query.where(and_(*filters))
    result = await db.execute(count_query)
    total = result.scalar() or 0

    # Get paginated leads
    query = select(Lead).order_by(desc(Lead.created_at))
    if filters:
        query = query.where(and_(*filters))
    query = query.limit(per_page).offset((page - 1) * per_page)

    result = await db.execute(query)
    leads = result.scalars().all()

    items = [
        {
            "id": str(lead.id),
            "platform_sender_id": lead.platform_sender_id,
            "platform": lead.platform.value,
            "name": lead.name,
            "phone": lead.phone,
            "email": lead.email,
            "interested_projects": lead.interested_projects,
            "budget_range": lead.budget_range,
            "timeline": lead.timeline,
            "status": lead.status.value,
            "notes": lead.notes,
            "last_message_at": lead.last_message_at.isoformat(),
            "created_at": lead.created_at.isoformat(),
            "updated_at": lead.updated_at.isoformat(),
        }
        for lead in leads
    ]

    pages = ceil(total / per_page) if total > 0 else 1

    return PaginatedResponse(
        items=items,
        page=page,
        per_page=per_page,
        total=total,
        pages=pages,
    )


@router.get("/leads/{lead_id}", response_model=LeadResponse)
async def get_lead(
    lead_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> LeadResponse:
    """Get single lead by ID."""
    result = await db.execute(
        select(Lead).where(Lead.id == lead_id)
    )
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    return LeadResponse(
        id=lead.id,
        platform_sender_id=lead.platform_sender_id,
        platform=lead.platform.value,
        name=lead.name,
        phone=lead.phone,
        email=lead.email,
        interested_projects=lead.interested_projects,
        budget_range=lead.budget_range,
        timeline=lead.timeline,
        status=lead.status.value,
        notes=lead.notes,
        last_message_at=lead.last_message_at,
        created_at=lead.created_at,
        updated_at=lead.updated_at,
    )


@router.patch("/leads/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: UUID,
    update_data: LeadUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> LeadResponse:
    """Update lead fields."""
    result = await db.execute(
        select(Lead).where(Lead.id == lead_id)
    )
    lead = result.scalar_one_or_none()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    # Update only provided fields
    if update_data.status is not None:
        try:
            lead.status = LeadStatus(update_data.status)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status value")
    if update_data.notes is not None:
        lead.notes = update_data.notes
    if update_data.name is not None:
        lead.name = update_data.name
    if update_data.phone is not None:
        lead.phone = update_data.phone

    await db.commit()
    await db.refresh(lead)

    return LeadResponse(
        id=lead.id,
        platform_sender_id=lead.platform_sender_id,
        platform=lead.platform.value,
        name=lead.name,
        phone=lead.phone,
        email=lead.email,
        interested_projects=lead.interested_projects,
        budget_range=lead.budget_range,
        timeline=lead.timeline,
        status=lead.status.value,
        notes=lead.notes,
        last_message_at=lead.last_message_at,
        created_at=lead.created_at,
        updated_at=lead.updated_at,
    )


@router.get("/leads/{lead_id}/conversations", response_model=list[ConversationResponse])
async def get_lead_conversations(
    lead_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> list[ConversationResponse]:
    """Get all conversations for a lead."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.lead_id == lead_id)
        .order_by(desc(Conversation.started_at))
    )
    conversations = result.scalars().all()

    return [
        ConversationResponse(
            id=conv.id,
            lead_id=conv.lead_id,
            platform=conv.platform,
            started_at=conv.started_at,
            last_message_at=conv.last_message_at,
            message_count=conv.message_count,
            summary=conv.summary,
        )
        for conv in conversations
    ]


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_conversation_messages(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: str = Depends(verify_api_key),
) -> list[MessageResponse]:
    """Get all messages in a conversation ordered by timestamp."""
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.timestamp)
    )
    messages = result.scalars().all()

    return [
        MessageResponse(
            id=msg.id,
            conversation_id=msg.conversation_id,
            sender_type=msg.sender_type.value,
            content=msg.content,
            platform=msg.platform,
            timestamp=msg.timestamp,
        )
        for msg in messages
    ]


@router.get("/properties")
async def get_properties(
    _: str = Depends(verify_api_key),
) -> dict:
    """Load and return properties from data/properties.json."""
    properties_path = Path(__file__).parent.parent.parent / "data" / "properties.json"

    if not properties_path.exists():
        logger.warning(f"Properties file not found at {properties_path}")
        return {}

    try:
        with open(properties_path, "r", encoding="utf-8") as f:
            properties = json.load(f)
        return properties
    except Exception as e:
        logger.error(f"Error loading properties: {e}")
        return {}
