import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import ForeignKey, String, DateTime, Numeric, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ReconciliationType


class Reconciliation(Base):
    __tablename__ = "reconciliations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[ReconciliationType] = mapped_column(
        String(20), nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="confirmed", index=True
    )
    reconciliation_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    confirmed_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    matching_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    applied_rule: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    company: Mapped["Company"] = relationship(back_populates="reconciliations")  # noqa: F821
    confirmed_by_user: Mapped["User"] = relationship(lazy="selectin")  # noqa: F821
    lines: Mapped[list["ReconciliationLine"]] = relationship(  # noqa: F821
        back_populates="reconciliation", lazy="selectin", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_reconciliations_company_status", "company_id", "status"),
        Index("ix_reconciliations_company_date", "company_id", "reconciliation_date"),
    )
