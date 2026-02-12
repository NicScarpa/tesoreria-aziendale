import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Index, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import AlertStatus, CashFlowAlertType


class CashFlowAlert(Base):
    __tablename__ = "cash_flow_alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    forecast_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cash_flow_forecasts.id", ondelete="SET NULL"),
        nullable=True,
    )
    tipo: Mapped[CashFlowAlertType] = mapped_column(
        Enum(CashFlowAlertType, name="cash_flow_alert_type",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    data_prevista: Mapped[date] = mapped_column(Date, nullable=False)
    saldo_previsto: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    soglia: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    messaggio: Mapped[str] = mapped_column(Text, nullable=False)
    stato: Mapped[AlertStatus] = mapped_column(
        Enum(AlertStatus, name="alert_status",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=AlertStatus.ATTIVO,
    )
    notificato: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notificato_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
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

    # Relationships
    company: Mapped["Company"] = relationship()  # noqa: F821
    forecast: Mapped["CashFlowForecast | None"] = relationship(back_populates="alerts")  # noqa: F821

    __table_args__ = (
        Index("ix_cf_alerts_company_stato_data", "company_id", "stato", "data_prevista"),
        Index("ix_cf_alerts_company_tipo_stato", "company_id", "tipo", "stato"),
    )
