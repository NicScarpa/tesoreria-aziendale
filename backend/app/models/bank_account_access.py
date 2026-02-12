import uuid
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, DateTime, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import AccessLevel


class BankAccountAccess(Base):
    __tablename__ = "bank_account_accesses"
    __table_args__ = (
        UniqueConstraint("bank_account_id", "user_id", name="uq_bank_account_user_access"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    bank_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bank_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    access_level: Mapped[AccessLevel] = mapped_column(
        Enum(AccessLevel, name="access_level", create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=AccessLevel.READ,
    )
    granted_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
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

    bank_account: Mapped["BankAccount"] = relationship(back_populates="accesses")  # noqa: F821
    user: Mapped["User"] = relationship(foreign_keys=[user_id], lazy="selectin")  # noqa: F821
    grantor: Mapped["User"] = relationship(foreign_keys=[granted_by], lazy="selectin")  # noqa: F821
