import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import ForeignKey, Date, DateTime, Numeric, Enum, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import BalanceSource


class BankAccountBalance(Base):
    __tablename__ = "bank_account_balances"
    __table_args__ = (
        UniqueConstraint("bank_account_id", "balance_date", name="uq_bank_account_balance_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    bank_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bank_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    balance_date: Mapped[date] = mapped_column(Date, nullable=False)
    current_balance: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    available_balance: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    source: Mapped[BalanceSource] = mapped_column(
        Enum(BalanceSource, name="balance_source", create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    bank_account: Mapped["BankAccount"] = relationship(back_populates="balances")  # noqa: F821
