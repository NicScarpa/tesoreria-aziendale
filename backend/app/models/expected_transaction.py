import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import ForeignKey, String, Date, DateTime, Numeric, Enum, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import (
    ExpectedTransactionType, ExpectedDocumentType,
    ExpectedTransactionStatus, ExpectedTransactionSource,
)


class ExpectedTransaction(Base):
    __tablename__ = "expected_transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    bank_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bank_accounts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    counterpart_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    counterpart_iban: Mapped[str | None] = mapped_column(String(34), nullable=True)
    type: Mapped[ExpectedTransactionType] = mapped_column(
        Enum(ExpectedTransactionType, name="expected_transaction_type",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    expected_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_number: Mapped[str | None] = mapped_column(String(255), nullable=True)
    document_type: Mapped[ExpectedDocumentType] = mapped_column(
        Enum(ExpectedDocumentType, name="expected_document_type",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=ExpectedDocumentType.OTHER,
    )
    status: Mapped[ExpectedTransactionStatus] = mapped_column(
        Enum(ExpectedTransactionStatus, name="expected_transaction_status",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=ExpectedTransactionStatus.OPEN, index=True,
    )
    matched_amount: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0")
    )
    schedule_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schedules.id", ondelete="SET NULL"),
        nullable=True,
    )
    source: Mapped[ExpectedTransactionSource] = mapped_column(
        Enum(ExpectedTransactionSource, name="expected_transaction_source",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=ExpectedTransactionSource.MANUAL,
    )
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    company: Mapped["Company"] = relationship(back_populates="expected_transactions")  # noqa: F821
    bank_account: Mapped["BankAccount"] = relationship(lazy="selectin")  # noqa: F821
    reconciliation_lines: Mapped[list["ReconciliationLine"]] = relationship(  # noqa: F821
        back_populates="expected_transaction", lazy="select"
    )
    schedule: Mapped["Schedule | None"] = relationship(  # noqa: F821
        foreign_keys=[schedule_id], lazy="selectin",
    )

    __table_args__ = (
        Index("ix_expected_transactions_company_status_due", "company_id", "status", "due_date"),
        Index("ix_expected_transactions_company_type_status", "company_id", "type", "status"),
        Index("ix_expected_transactions_ref_company", "reference_number", "company_id"),
    )
