import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Institution(Base):
    __tablename__ = "institutions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="SWAN")
    types: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    country: Mapped[str] = mapped_column(String(2), default="IT", nullable=False)
    bic: Mapped[str | None] = mapped_column(String(11), nullable=True, index=True)
    hidden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    icon_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    bank_connections: Mapped[list["BankConnection"]] = relationship(  # noqa: F821
        back_populates="institution", lazy="select"
    )
