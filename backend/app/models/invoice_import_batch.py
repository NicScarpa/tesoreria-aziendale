import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    DateTime, Enum, ForeignKey, Integer, Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import InvoiceBatchSource, InvoiceBatchStatus


class InvoiceImportBatch(Base):
    __tablename__ = "invoice_import_batches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    fonte: Mapped[InvoiceBatchSource] = mapped_column(
        Enum(InvoiceBatchSource, name="invoice_batch_source",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    data_import: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    totale_fatture: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fatture_importate: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fatture_errore: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fatture_duplicate: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    stato: Mapped[InvoiceBatchStatus] = mapped_column(
        Enum(InvoiceBatchStatus, name="invoice_batch_status",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=InvoiceBatchStatus.IN_CORSO,
    )
    importato_da_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
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

    company: Mapped["Company"] = relationship(back_populates="invoice_import_batches")  # noqa: F821
    invoices: Mapped[list["InvoiceImport"]] = relationship(  # noqa: F821
        back_populates="batch", lazy="select",
    )

    __table_args__ = (
        Index("ix_invoice_import_batches_company_data", "company_id", "data_import"),
    )
