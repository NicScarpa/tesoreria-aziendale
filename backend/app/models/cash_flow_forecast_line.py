import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import CashFlowLineType, CashFlowSource, ConfidenceLevel


class CashFlowForecastLine(Base):
    __tablename__ = "cash_flow_forecast_lines"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    forecast_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cash_flow_forecasts.id", ondelete="CASCADE"),
        nullable=False,
    )
    data: Mapped[date] = mapped_column(Date, nullable=False)
    tipo: Mapped[CashFlowLineType] = mapped_column(
        Enum(CashFlowLineType, name="cash_flow_line_type",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    importo: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    categoria: Mapped[str | None] = mapped_column(String(255), nullable=True)
    descrizione: Mapped[str | None] = mapped_column(Text, nullable=True)
    fonte: Mapped[CashFlowSource] = mapped_column(
        Enum(CashFlowSource, name="cash_flow_source",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    fonte_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    confidenza: Mapped[ConfidenceLevel] = mapped_column(
        Enum(ConfidenceLevel, name="confidence_level",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=ConfidenceLevel.MEDIA,
    )
    saldo_progressivo: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0")
    )
    is_realizzata: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    varianza: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

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
    forecast: Mapped["CashFlowForecast"] = relationship(back_populates="lines")  # noqa: F821

    __table_args__ = (
        Index("ix_cf_lines_forecast_data", "forecast_id", "data"),
        Index("ix_cf_lines_forecast_fonte", "forecast_id", "fonte"),
        Index("ix_cf_lines_forecast_tipo_data", "forecast_id", "tipo", "data"),
        Index("ix_cf_lines_fonte_id", "fonte_id"),
    )
