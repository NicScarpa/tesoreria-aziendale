import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Boolean, Date, DateTime, Enum, ForeignKey, Integer,
    Numeric, String, Text, Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import (
    DocumentType, PaymentMethod, RecurrenceType,
    SchedulePriority, ScheduleSource, ScheduleStatus, ScheduleType,
)


class Schedule(Base):
    __tablename__ = "schedules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    tipo: Mapped[ScheduleType] = mapped_column(
        Enum(ScheduleType, name="schedule_type",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    stato: Mapped[ScheduleStatus] = mapped_column(
        Enum(ScheduleStatus, name="schedule_status",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=ScheduleStatus.APERTA,
    )
    descrizione: Mapped[str] = mapped_column(String(500), nullable=False)
    importo_totale: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    importo_pagato: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0")
    )
    valuta: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)
    data_scadenza: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    data_emissione: Mapped[date | None] = mapped_column(Date, nullable=True)
    data_pagamento: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Documento
    tipo_documento: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, name="document_type",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=DocumentType.ALTRO,
    )
    numero_documento: Mapped[str | None] = mapped_column(String(100), nullable=True)
    riferimento_documento: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Controparte
    controparte_nome: Mapped[str | None] = mapped_column(String(255), nullable=True)
    controparte_iban: Mapped[str | None] = mapped_column(String(34), nullable=True)
    counterparty_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True,
    )

    # Conto bancario
    bank_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bank_accounts.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )

    # Priorita e classificazione
    priorita: Mapped[SchedulePriority] = mapped_column(
        Enum(SchedulePriority, name="schedule_priority",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=SchedulePriority.NORMALE,
    )
    metodo_pagamento: Mapped[PaymentMethod | None] = mapped_column(
        Enum(PaymentMethod, name="payment_method",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=True,
    )
    categoria_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Origine
    source: Mapped[ScheduleSource] = mapped_column(
        Enum(ScheduleSource, name="schedule_source",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=ScheduleSource.MANUALE,
    )

    # Ricorrenza
    is_ricorrente: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ricorrenza_tipo: Mapped[RecurrenceType | None] = mapped_column(
        Enum(RecurrenceType, name="recurrence_type",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=True,
    )
    ricorrenza_fine: Mapped[date | None] = mapped_column(Date, nullable=True)
    ricorrenza_prossima_generazione: Mapped[date | None] = mapped_column(Date, nullable=True)
    ricorrenza_parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schedules.id", ondelete="SET NULL"),
        nullable=True,
    )
    ricorrenza_attiva: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Collegamento ExpectedTransaction
    expected_transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("expected_transactions.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Note e metadata
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

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
    company: Mapped["Company"] = relationship(back_populates="schedules")  # noqa: F821
    bank_account: Mapped["BankAccount"] = relationship(lazy="selectin")  # noqa: F821
    expected_transaction: Mapped["ExpectedTransaction | None"] = relationship(  # noqa: F821
        foreign_keys=[expected_transaction_id], lazy="selectin",
    )
    payments: Mapped[list["SchedulePayment"]] = relationship(  # noqa: F821
        back_populates="schedule", cascade="all, delete-orphan", lazy="selectin",
    )
    reminders: Mapped[list["ScheduleReminder"]] = relationship(  # noqa: F821
        back_populates="schedule", cascade="all, delete-orphan", lazy="select",
    )
    attachments: Mapped[list["ScheduleAttachment"]] = relationship(  # noqa: F821
        back_populates="schedule", cascade="all, delete-orphan", lazy="select",
    )
    ricorrenza_parent: Mapped["Schedule | None"] = relationship(
        remote_side="Schedule.id", foreign_keys=[ricorrenza_parent_id], lazy="select",
    )
    ricorrenza_figli: Mapped[list["Schedule"]] = relationship(
        back_populates="ricorrenza_parent", foreign_keys=[ricorrenza_parent_id], lazy="select",
    )

    @hybrid_property
    def importo_residuo(self) -> Decimal:
        return self.importo_totale - self.importo_pagato

    __table_args__ = (
        Index("ix_schedules_company_stato_scadenza", "company_id", "stato", "data_scadenza"),
        Index("ix_schedules_company_tipo_stato", "company_id", "tipo", "stato"),
        Index("ix_schedules_company_counterparty", "company_id", "counterparty_id"),
        Index("ix_schedules_company_data_scadenza", "company_id", "data_scadenza"),
        Index("ix_schedules_company_stato_priorita", "company_id", "stato", "priorita"),
        Index("ix_schedules_company_ricorrente_prossima", "company_id", "is_ricorrente", "ricorrenza_prossima_generazione"),
    )
