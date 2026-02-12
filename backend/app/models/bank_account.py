import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import ForeignKey, String, Boolean, DateTime, Numeric, Enum, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import AccountStatus, AccountType


class BankAccount(Base):
    __tablename__ = "bank_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    bank_connection_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bank_connections.id", ondelete="SET NULL"), nullable=True
    )
    nickname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    iban: Mapped[str | None] = mapped_column(String(34), nullable=True, index=True)
    bic: Mapped[str | None] = mapped_column(String(11), nullable=True)
    account_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="EUR", nullable=False)
    current_balance: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    available_balance: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    balance_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    credit_limit: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    status: Mapped[AccountStatus] = mapped_column(
        Enum(AccountStatus, name="account_status", create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=AccountStatus.ACTIVE,
    )
    ignore_balance: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    hidden_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    allow_balance_change: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    provider_account_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    identifiers: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=list)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    account_type: Mapped[AccountType | None] = mapped_column(
        Enum(AccountType, name="account_type", create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=True,
    )
    color: Mapped[str | None] = mapped_column(String(7), default="#6b7280", nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    bank_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    bank_abi: Mapped[str | None] = mapped_column(String(5), nullable=True)
    bank_cab: Mapped[str | None] = mapped_column(String(5), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    company: Mapped["Company"] = relationship(back_populates="bank_accounts")  # noqa: F821
    bank_connection: Mapped["BankConnection"] = relationship(back_populates="bank_accounts")  # noqa: F821
    balances: Mapped[list["BankAccountBalance"]] = relationship(  # noqa: F821
        back_populates="bank_account", lazy="select", cascade="all, delete-orphan"
    )
    accesses: Mapped[list["BankAccountAccess"]] = relationship(  # noqa: F821
        back_populates="bank_account", lazy="select", cascade="all, delete-orphan"
    )
    transactions: Mapped[list["Transaction"]] = relationship(  # noqa: F821
        back_populates="bank_account", lazy="select", cascade="all, delete-orphan"
    )
