"""Admin API request/response schemas."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from typing import Any


class DashboardStats(BaseModel):
    """Dashboard statistics response."""
    model_config = ConfigDict(from_attributes=True)

    leads_today: int = 0
    leads_this_week: int = 0
    leads_this_month: int = 0
    leads_by_platform: dict[str, int] = {}
    leads_by_status: dict[str, int] = {}
    top_projects: list[dict[str, Any]] = []
    recent_leads: list[dict[str, Any]] = []


class LeadResponse(BaseModel):
    """Single lead response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    platform_sender_id: str
    platform: str
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    interested_projects: list | None = None
    budget_range: str | None = None
    timeline: str | None = None
    status: str
    notes: str | None = None
    last_message_at: datetime
    created_at: datetime
    updated_at: datetime


class LeadUpdateRequest(BaseModel):
    """Request to update a lead."""
    status: str | None = None
    notes: str | None = None
    name: str | None = None
    phone: str | None = None


class PaginatedResponse(BaseModel):
    """Paginated list response."""
    items: list[dict[str, Any]]
    page: int
    per_page: int
    total: int
    pages: int


class MessageResponse(BaseModel):
    """Single message response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    sender_type: str
    content: str
    platform: str
    timestamp: datetime


class ConversationResponse(BaseModel):
    """Single conversation response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lead_id: UUID
    platform: str
    started_at: datetime
    last_message_at: datetime
    message_count: int
    summary: str | None = None
