import uuid
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ConsentStatus, ConsentPurpose


class BankConnection(Base):
    __tablename__ = "bank_connections"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[ConsentStatus] = mapped_column(
        Enum(ConsentStatus, name="consent_status", create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ConsentStatus.PENDING,
    )
    purpose: Mapped[ConsentPurpose] = mapped_column(
        Enum(ConsentPurpose, name="consent_purpose", create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ConsentPurpose.AISP,
    )
    provider_source_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    authorized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    company: Mapped["Company"] = relationship(back_populates="bank_connections")  # noqa: F821
    user: Mapped["User"] = relationship(lazy="selectin")  # noqa: F821
    institution: Mapped["Institution"] = relationship(back_populates="bank_connections")  # noqa: F821
    bank_accounts: Mapped[list["BankAccount"]] = relationship(  # noqa: F821
        back_populates="bank_connection", lazy="selectin"
    )
