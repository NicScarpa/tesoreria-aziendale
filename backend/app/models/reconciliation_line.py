import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import ForeignKey, DateTime, Numeric, Text, Enum, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ReconciliationLineType


class ReconciliationLine(Base):
    __tablename__ = "reconciliation_lines"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    reconciliation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reconciliations.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transactions.id", ondelete="SET NULL"),
        nullable=True, index=True
    )
    expected_transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("expected_transactions.id", ondelete="SET NULL"),
        nullable=True, index=True
    )
    matched_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    line_type: Mapped[ReconciliationLineType] = mapped_column(
        Enum(ReconciliationLineType, name="reconciliation_line_type",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=ReconciliationLineType.TRANSACTION_MATCH,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    reconciliation: Mapped["Reconciliation"] = relationship(back_populates="lines")  # noqa: F821
    transaction: Mapped["Transaction"] = relationship(lazy="selectin")  # noqa: F821
    expected_transaction: Mapped["ExpectedTransaction"] = relationship(  # noqa: F821
        back_populates="reconciliation_lines", lazy="selectin"
    )

    __table_args__ = (
        CheckConstraint(
            "transaction_id IS NOT NULL OR expected_transaction_id IS NOT NULL",
            name="ck_reconciliation_line_has_ref",
        ),
    )
