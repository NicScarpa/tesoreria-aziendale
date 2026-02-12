import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Date, DateTime, Enum, ForeignKey, Numeric, String, Text, Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import InvoiceDocumentType, InvoiceSource, InvoiceStatus


class InvoiceImport(Base):
    __tablename__ = "invoice_imports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    batch_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("invoice_import_batches.id", ondelete="SET NULL"),
        nullable=True,
    )
    fonte: Mapped[InvoiceSource] = mapped_column(
        Enum(InvoiceSource, name="invoice_source",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    tipo_documento: Mapped[InvoiceDocumentType] = mapped_column(
        Enum(InvoiceDocumentType, name="invoice_document_type",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    stato: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus, name="invoice_status",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=InvoiceStatus.IMPORTATA,
    )

    # Dati fattura
    numero_fattura: Mapped[str | None] = mapped_column(String(100), nullable=True)
    data_fattura: Mapped[date | None] = mapped_column(Date, nullable=True)
    cedente_denominazione: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cedente_piva: Mapped[str | None] = mapped_column(String(20), nullable=True)
    cedente_cf: Mapped[str | None] = mapped_column(String(20), nullable=True)
    cessionario_denominazione: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cessionario_piva: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Importi
    importo_totale: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    imponibile_totale: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    iva_totale: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    valuta: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)

    # Pagamento
    condizioni_pagamento: Mapped[str | None] = mapped_column(String(100), nullable=True)
    modalita_pagamento: Mapped[str | None] = mapped_column(String(100), nullable=True)
    data_scadenza_pagamento: Mapped[date | None] = mapped_column(Date, nullable=True)
    iban_pagamento: Mapped[str | None] = mapped_column(String(34), nullable=True)

    # File
    xml_file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    xml_file_nome: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pdf_allegato_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Identificativi
    identificativo_sdi: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Collegamenti
    schedule_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schedules.id", ondelete="SET NULL"),
        nullable=True,
    )
    counterparty_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True,
    )
    expected_transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("expected_transactions.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Errore
    errore_dettaglio: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Utente
    elaborato_da_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Timestamps
    data_importazione: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    data_elaborazione: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    metadata_extra: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    company: Mapped["Company"] = relationship(back_populates="invoice_imports")  # noqa: F821
    batch: Mapped["InvoiceImportBatch"] = relationship(back_populates="invoices")  # noqa: F821
    schedule: Mapped["Schedule"] = relationship(lazy="selectin")  # noqa: F821

    __table_args__ = (
        Index("ix_invoice_imports_company_tipo_stato", "company_id", "tipo_documento", "stato"),
        Index("ix_invoice_imports_company_data", "company_id", "data_fattura"),
        Index("ix_invoice_imports_cedente_piva", "cedente_piva", "company_id"),
        Index("ix_invoice_imports_numero_cedente", "numero_fattura", "cedente_piva", "company_id"),
    )
