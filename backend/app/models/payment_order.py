import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    Date, DateTime, Enum, ForeignKey, Integer,
    Numeric, String, Text, Index, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import (
    PaymentOrderStatus, PaymentOrderType, PaymentPriority,
)


class PaymentOrder(Base):
    __tablename__ = "payment_orders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    bank_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bank_accounts.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    tipo: Mapped[PaymentOrderType] = mapped_column(
        Enum(PaymentOrderType, name="payment_order_type",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    stato: Mapped[PaymentOrderStatus] = mapped_column(
        Enum(PaymentOrderStatus, name="payment_order_status",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=PaymentOrderStatus.BOZZA,
    )
    riferimento_interno: Mapped[str] = mapped_column(String(50), nullable=False)
    data_esecuzione_richiesta: Mapped[date] = mapped_column(Date, nullable=False)
    importo_totale: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0")
    )
    numero_disposizioni: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    valuta: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)
    priorita: Mapped[PaymentPriority] = mapped_column(
        Enum(PaymentPriority, name="payment_priority",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=PaymentPriority.NORMALE,
    )

    # SEPA/formato metadata
    metadata_sepa: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    metadata_extra: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # File generato
    file_generato_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_generato_nome: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_generato_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    file_esito_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Approvazione
    approvato_da_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    data_approvazione: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Creazione
    creato_da_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

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
    company: Mapped["Company"] = relationship(back_populates="payment_orders")  # noqa: F821
    bank_account: Mapped["BankAccount"] = relationship(lazy="selectin")  # noqa: F821
    lines: Mapped[list["PaymentOrderLine"]] = relationship(  # noqa: F821
        back_populates="payment_order", cascade="all, delete-orphan", lazy="selectin",
    )
    approvals: Mapped[list["PaymentApproval"]] = relationship(  # noqa: F821
        back_populates="payment_order", cascade="all, delete-orphan", lazy="select",
    )
    created_by_user: Mapped["User"] = relationship(  # noqa: F821
        foreign_keys=[creato_da_user_id], lazy="selectin",
    )
    approved_by_user: Mapped["User | None"] = relationship(  # noqa: F821
        foreign_keys=[approvato_da_user_id], lazy="selectin",
    )

    __table_args__ = (
        Index("ix_payment_orders_company_stato", "company_id", "stato"),
        Index("ix_payment_orders_company_data_esecuzione", "company_id", "data_esecuzione_richiesta"),
        Index("ix_payment_orders_company_tipo_stato", "company_id", "tipo", "stato"),
        UniqueConstraint("riferimento_interno", "company_id", name="uq_payment_orders_riferimento_company"),
    )
