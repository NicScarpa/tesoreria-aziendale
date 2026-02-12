import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Date, DateTime, Enum, ForeignKey, Integer,
    Numeric, String, Text, Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import (
    F24SectionType, PaymentLineStatus, SDDMandateType, SDDSequenceType,
)


class PaymentOrderLine(Base):
    __tablename__ = "payment_order_lines"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    payment_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payment_orders.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )

    # Beneficiario
    beneficiario_nome: Mapped[str] = mapped_column(String(255), nullable=False)
    beneficiario_iban: Mapped[str | None] = mapped_column(String(34), nullable=True)
    beneficiario_bic: Mapped[str | None] = mapped_column(String(11), nullable=True)
    beneficiario_cf: Mapped[str | None] = mapped_column(String(16), nullable=True)
    beneficiario_indirizzo: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Dati pagamento
    importo: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    valuta: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)
    causale: Mapped[str | None] = mapped_column(String(140), nullable=True)
    end_to_end_id: Mapped[str | None] = mapped_column(String(35), nullable=True)

    # Stato riga
    stato: Mapped[PaymentLineStatus] = mapped_column(
        Enum(PaymentLineStatus, name="payment_line_status",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=PaymentLineStatus.INCLUSA,
    )

    # FK opzionali
    counterparty_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True,
    )
    schedule_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schedules.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )

    # Campi RiBa
    riba_numero_ricevuta: Mapped[str | None] = mapped_column(String(10), nullable=True)
    riba_data_scadenza: Mapped[date | None] = mapped_column(Date, nullable=True)
    riba_piazza: Mapped[str | None] = mapped_column(String(50), nullable=True)
    riba_abi_banca_domiciliataria: Mapped[str | None] = mapped_column(String(5), nullable=True)
    riba_cab_banca_domiciliataria: Mapped[str | None] = mapped_column(String(5), nullable=True)

    # Campi SDD
    sdd_mandate_id: Mapped[str | None] = mapped_column(String(35), nullable=True)
    sdd_mandate_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    sdd_mandate_type: Mapped[SDDMandateType | None] = mapped_column(
        Enum(SDDMandateType, name="sdd_mandate_type",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=True,
    )
    sdd_sequence_type: Mapped[SDDSequenceType | None] = mapped_column(
        Enum(SDDSequenceType, name="sdd_sequence_type",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=True,
    )

    # Campi F24
    f24_sezione: Mapped[F24SectionType | None] = mapped_column(
        Enum(F24SectionType, name="f24_section_type",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=True,
    )
    f24_codice_tributo: Mapped[str | None] = mapped_column(String(10), nullable=True)
    f24_rateazione: Mapped[str | None] = mapped_column(String(4), nullable=True)
    f24_anno_riferimento: Mapped[int | None] = mapped_column(Integer, nullable=True)
    f24_mese_riferimento: Mapped[int | None] = mapped_column(Integer, nullable=True)
    f24_importo_debito: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    f24_importo_credito: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    f24_codice_ente: Mapped[str | None] = mapped_column(String(10), nullable=True)
    f24_codice_sede: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Metadata extra
    metadata_extra: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Timestamps
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
    payment_order: Mapped["PaymentOrder"] = relationship(back_populates="lines")  # noqa: F821
    schedule: Mapped["Schedule | None"] = relationship(lazy="selectin")  # noqa: F821

    __table_args__ = (
        Index("ix_payment_order_lines_stato", "stato"),
    )
