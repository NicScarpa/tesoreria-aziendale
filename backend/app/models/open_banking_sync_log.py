import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import SyncLogStatus


class OpenBankingSyncLog(Base):
    __tablename__ = "open_banking_sync_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    connection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("open_banking_connections.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    data_sync: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    stato: Mapped[SyncLogStatus] = mapped_column(
        Enum(SyncLogStatus, name="sync_log_status",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    movimenti_scaricati: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    movimenti_nuovi: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    movimenti_duplicati: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    saldo_aggiornato: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    periodo_da: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    periodo_a: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    durata_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    errore_dettaglio: Mapped[str | None] = mapped_column(Text, nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    connection: Mapped["OpenBankingConnection"] = relationship(back_populates="sync_logs")  # noqa: F821

    __table_args__ = (
        Index("ix_ob_sync_logs_connection_data", "connection_id", "data_sync"),
    )
