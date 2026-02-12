import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Date, DateTime, Index, Integer, Numeric, UniqueConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DashboardSnapshot(Base):
    __tablename__ = "dashboard_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    data: Mapped[date] = mapped_column(Date, nullable=False)
    saldo_totale: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    entrate_giorno: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    uscite_giorno: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    movimenti_non_riconciliati: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    scadenze_scadute_importo: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    scadenze_scadute_conteggio: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    pagamenti_da_approvare: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    previsione_30gg: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False, default=Decimal("0"))
    alert_attivi: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metadata_extra: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    company: Mapped["Company"] = relationship()  # noqa: F821

    __table_args__ = (
        UniqueConstraint("company_id", "data", name="uq_dashboard_snapshot_company_data"),
        Index("ix_dashboard_snapshots_company_data", "company_id", "data"),
    )
