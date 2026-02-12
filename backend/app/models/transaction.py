import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import ForeignKey, String, Boolean, DateTime, Date, Numeric, Enum, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import (
    FlowDirection, TransactionStatus, TransactionType, CategorizationSource,
    ReconciliationStatus,
)


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    bank_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bank_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)
    direction: Mapped[FlowDirection] = mapped_column(
        Enum(FlowDirection, name="flow_direction", create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    transaction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    value_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    remittance_info: Mapped[str | None] = mapped_column(Text, nullable=True)
    transaction_type: Mapped[TransactionType] = mapped_column(
        Enum(TransactionType, name="transaction_type", create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=TransactionType.OTHER,
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    subcategory_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subcategories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    categorization_source: Mapped[CategorizationSource | None] = mapped_column(
        Enum(CategorizationSource, name="categorization_source", create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=True,
    )
    counterpart_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    counterpart_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    counterpart_iban: Mapped[str | None] = mapped_column(String(34), nullable=True)
    status: Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus, name="transaction_status", create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=TransactionStatus.BOOKED, index=True,
    )
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    provider_transaction_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    hidden_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True, default=dict)
    reconciliation_status: Mapped[ReconciliationStatus] = mapped_column(
        Enum(ReconciliationStatus, name="reconciliation_status", create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=ReconciliationStatus.UNRECONCILED, index=True,
    )
    reconciliation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reconciliations.id", ondelete="SET NULL"), nullable=True
    )
    import_batch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("import_batches.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    company: Mapped["Company"] = relationship(back_populates="transactions")  # noqa: F821
    bank_account: Mapped["BankAccount"] = relationship(back_populates="transactions")  # noqa: F821
    category: Mapped["Category"] = relationship(lazy="selectin")  # noqa: F821
    subcategory: Mapped["Subcategory"] = relationship(lazy="selectin")  # noqa: F821
    import_batch: Mapped["ImportBatch"] = relationship(back_populates="transactions")  # noqa: F821
    allocations: Mapped[list["TransactionAllocation"]] = relationship(  # noqa: F821
        back_populates="transaction", lazy="selectin", cascade="all, delete-orphan"
    )
