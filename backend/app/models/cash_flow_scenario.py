import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import CashFlowLineType, ScenarioAdjustmentType


class CashFlowScenario(Base):
    __tablename__ = "cash_flow_scenarios"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    forecast_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cash_flow_forecasts.id", ondelete="CASCADE"),
        nullable=False,
    )
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    descrizione: Mapped[str | None] = mapped_column(Text, nullable=True)
    tipo_aggiustamento: Mapped[ScenarioAdjustmentType] = mapped_column(
        Enum(ScenarioAdjustmentType, name="scenario_adjustment_type",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    data_originale: Mapped[date | None] = mapped_column(Date, nullable=True)
    data_modificata: Mapped[date | None] = mapped_column(Date, nullable=True)
    importo_originale: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    importo_modificato: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    tipo_movimento: Mapped[CashFlowLineType | None] = mapped_column(
        Enum(CashFlowLineType, name="cash_flow_line_type",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=True,
    )
    categoria: Mapped[str | None] = mapped_column(String(255), nullable=True)
    attivo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

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
    forecast: Mapped["CashFlowForecast"] = relationship(back_populates="scenarios")  # noqa: F821

    __table_args__ = (
        Index("ix_cf_scenarios_forecast_attivo", "forecast_id", "attivo"),
    )
