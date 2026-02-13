"""
SQLAlchemy models for organizations.
"""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class Organization(Base):
    """Organization model for multi-tenancy."""

    __tablename__ = "organizations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    settings: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    branding: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, name={self.name}, slug={self.slug})>"
