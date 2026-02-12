import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import (
    OpenBankingConnectionStatus, OpenBankingProvider, SyncFrequency,
)


class OpenBankingConnection(Base):
    __tablename__ = "open_banking_connections"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    bank_account_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("bank_accounts.id", ondelete="SET NULL"),
        nullable=True,
    )
    provider: Mapped[OpenBankingProvider] = mapped_column(
        Enum(OpenBankingProvider, name="open_banking_provider",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    provider_connection_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    provider_account_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    institution_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    institution_nome: Mapped[str | None] = mapped_column(String(255), nullable=True)
    institution_logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    stato: Mapped[OpenBankingConnectionStatus] = mapped_column(
        Enum(OpenBankingConnectionStatus, name="open_banking_connection_status",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=OpenBankingConnectionStatus.IN_ATTESA_CONSENSO,
    )
    consenso_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    consenso_scadenza: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    consenso_creato_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    ultimo_sync: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    prossimo_sync: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    frequenza_sync: Mapped[SyncFrequency] = mapped_column(
        Enum(SyncFrequency, name="sync_frequency",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=SyncFrequency.GIORNALIERO,
    )
    sync_attivo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    errore_ultimo: Mapped[str | None] = mapped_column(Text, nullable=True)
    errore_conteggio: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    metadata_provider: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    company: Mapped["Company"] = relationship(back_populates="open_banking_connections")  # noqa: F821
    bank_account: Mapped["BankAccount"] = relationship(lazy="selectin")  # noqa: F821
    sync_logs: Mapped[list["OpenBankingSyncLog"]] = relationship(  # noqa: F821
        back_populates="connection", cascade="all, delete-orphan", lazy="select",
    )

    __table_args__ = (
        Index("ix_ob_connections_company_stato", "company_id", "stato"),
        Index("ix_ob_connections_company_bank_account", "company_id", "bank_account_id"),
        Index("ix_ob_connections_prossimo_sync", "prossimo_sync", "sync_attivo", "stato"),
    )
