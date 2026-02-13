"""SQLAlchemy models for clients."""
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class Client(Base):
    """Client model for organizations."""

    __tablename__ = "clients"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_info: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    settings: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<Client(id={self.id}, name={self.name})>"
