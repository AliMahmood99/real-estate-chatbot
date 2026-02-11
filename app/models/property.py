"""Property database models (Project and Unit)."""

import uuid

from sqlalchemy import ForeignKey, JSON, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Project(Base):
    """Real estate project model."""

    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    developer: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str] = mapped_column(String(500), nullable=False)
    area: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    amenities: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    delivery_status: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    units = relationship("Unit", back_populates="project", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Project {self.name}>"


class Unit(Base):
    """Property unit model (apartment, villa, etc.)."""

    __tablename__ = "units"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_from: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    size_to: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    price_from: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    price_to: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    floor_options: Mapped[str | None] = mapped_column(String(255), nullable=True)
    views: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    payment_plans: Mapped[list | None] = mapped_column(JSON, nullable=True, default=list)
    availability_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="available"
    )

    # Relationships
    project = relationship("Project", back_populates="units")

    def __repr__(self) -> str:
        return f"<Unit {self.type} in project={self.project_id}>"
