import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import PaymentMethod


class SchedulePayment(Base):
    __tablename__ = "schedule_payments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    schedule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schedules.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    importo: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    data_pagamento: Mapped[date] = mapped_column(Date, nullable=False)
    metodo: Mapped[PaymentMethod | None] = mapped_column(
        Enum(PaymentMethod, name="payment_method",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=True,
    )
    riferimento: Mapped[str | None] = mapped_column(String(255), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    reconciliation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    schedule: Mapped["Schedule"] = relationship(back_populates="payments")  # noqa: F821
