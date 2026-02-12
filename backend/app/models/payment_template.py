import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import PaymentOrderType


class PaymentTemplate(Base):
    __tablename__ = "payment_templates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo: Mapped[PaymentOrderType] = mapped_column(
        Enum(PaymentOrderType, name="payment_order_type",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    bank_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bank_accounts.id", ondelete="SET NULL"),
        nullable=True,
    )
    dati_template: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    ultimo_utilizzo: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    volte_utilizzato: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

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
    company: Mapped["Company"] = relationship(back_populates="payment_templates")  # noqa: F821
    bank_account: Mapped["BankAccount"] = relationship(lazy="selectin")  # noqa: F821

    __table_args__ = (
        Index("ix_payment_templates_company_tipo", "company_id", "tipo"),
    )
