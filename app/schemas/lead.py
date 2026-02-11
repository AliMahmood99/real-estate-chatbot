"""Lead request/response schemas."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class LeadBase(BaseModel):
    """Base lead schema."""
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    budget_range: str | None = None
    timeline: str | None = None


class LeadCreate(LeadBase):
    """Schema for creating a lead."""
    platform_sender_id: str
    platform: str


class LeadUpdate(BaseModel):
    """Schema for updating a lead."""
    name: str | None = None
    phone: str | None = None
    status: str | None = None
    notes: str | None = None
    budget_range: str | None = None
    timeline: str | None = None
