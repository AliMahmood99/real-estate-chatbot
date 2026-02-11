"""Conversation and Message database models."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class SenderType(str, enum.Enum):
    """Message sender type."""
    CUSTOMER = "customer"
    BOT = "bot"


class Conversation(Base):
    """Conversation model tracking a chat session with a lead."""

    __tablename__ = "conversations"

    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    last_message_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    message_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    lead = relationship("Lead", back_populates="conversations")
    messages = relationship(
        "Message", back_populates="conversation", lazy="selectin",
        order_by="Message.timestamp"
    )

    def __repr__(self) -> str:
        return f"<Conversation {self.id} (lead={self.lead_id})>"


class Message(Base):
    """Message model for individual messages in a conversation."""

    __tablename__ = "messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_type: Mapped[SenderType] = mapped_column(
        Enum(SenderType), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message {self.sender_type.value} at {self.timestamp}>"
