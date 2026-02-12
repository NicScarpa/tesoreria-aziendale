import uuid
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, DateTime, Integer, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import BatchStatus


class ImportBatch(Base):
    __tablename__ = "import_batches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    bank_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bank_accounts.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    format: Mapped[str] = mapped_column(String(20), nullable=False)
    filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[BatchStatus] = mapped_column(
        Enum(BatchStatus, name="batch_status", create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=BatchStatus.PENDING,
    )
    total_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    imported_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    skipped_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    errors: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    company: Mapped["Company"] = relationship(back_populates="import_batches")  # noqa: F821
    bank_account: Mapped["BankAccount"] = relationship()  # noqa: F821
    transactions: Mapped[list["Transaction"]] = relationship(  # noqa: F821
        back_populates="import_batch", lazy="select"
    )
