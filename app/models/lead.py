"""Lead database model."""

import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Platform(str, enum.Enum):
    """Messaging platform enum."""
    WHATSAPP = "whatsapp"
    MESSENGER = "messenger"
    INSTAGRAM = "instagram"


class LeadStatus(str, enum.Enum):
    """Lead classification status."""
    NEW = "new"
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"
    CONVERTED = "converted"
    LOST = "lost"


class Lead(Base):
    """Lead model representing a potential customer."""

    __tablename__ = "leads"

    platform_sender_id: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )
    platform: Mapped[Platform] = mapped_column(
        Enum(Platform), nullable=False, index=True
    )
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    interested_projects: Mapped[list | None] = mapped_column(
        JSON, nullable=True, default=list
    )
    budget_range: Mapped[str | None] = mapped_column(String(255), nullable=True)
    timeline: Mapped[str | None] = mapped_column(String(255), nullable=True)
    preferred_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    preferred_size: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payment_plan: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[LeadStatus] = mapped_column(
        Enum(LeadStatus), nullable=False, default=LeadStatus.NEW, index=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_message_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    conversations = relationship("Conversation", back_populates="lead", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Lead {self.name or self.platform_sender_id} ({self.platform.value})>"
