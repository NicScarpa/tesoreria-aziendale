import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Date, DateTime, ForeignKey, Index, Numeric, String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ReceiptImport(Base):
    """
    Corrispettivi importati da Agenzia Entrate (Fatture e Corrispettivi).

    Nota: usiamo `idempotency_key` per garantire idempotenza senza dover creare
    indici parziali (es. external_id non sempre presente).
    """

    __tablename__ = "receipt_imports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    business_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)

    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    device_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    time_rilevazione: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    gross_total: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    net_total: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    vat_total: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)

    source: Mapped[str] = mapped_column(String(50), default="agenzia_entrate", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="imported", nullable=False)

    raw_attachment_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    errore_dettaglio: Mapped[str | None] = mapped_column(Text, nullable=True)
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

    company: Mapped["Company"] = relationship(back_populates="receipt_imports")  # noqa: F821

    __table_args__ = (
        UniqueConstraint("company_id", "idempotency_key", name="uq_receipt_imports_company_idempotency"),
        Index("ix_receipt_imports_company_date", "company_id", "business_date"),
        Index("ix_receipt_imports_company_external", "company_id", "external_id"),
        Index("ix_receipt_imports_company_device_date", "company_id", "device_id", "business_date"),
    )

