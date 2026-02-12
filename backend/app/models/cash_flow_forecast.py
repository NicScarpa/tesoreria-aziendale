import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ForecastStatus, ForecastType


class CashFlowForecast(Base):
    __tablename__ = "cash_flow_forecasts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    creato_da_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    descrizione: Mapped[str | None] = mapped_column(Text, nullable=True)
    data_inizio: Mapped[date] = mapped_column(Date, nullable=False)
    data_fine: Mapped[date] = mapped_column(Date, nullable=False)
    saldo_iniziale: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0")
    )
    saldo_finale_previsto: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0")
    )
    totale_entrate_previste: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0")
    )
    totale_uscite_previste: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=Decimal("0")
    )
    stato: Mapped[ForecastStatus] = mapped_column(
        Enum(ForecastStatus, name="forecast_status",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=ForecastStatus.BOZZA,
    )
    tipo: Mapped[ForecastType] = mapped_column(
        Enum(ForecastType, name="forecast_type",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=ForecastType.BASE,
    )
    parametri: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    is_auto: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

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
    company: Mapped["Company"] = relationship(back_populates="cash_flow_forecasts")  # noqa: F821
    creato_da: Mapped["User | None"] = relationship(lazy="selectin")  # noqa: F821
    lines: Mapped[list["CashFlowForecastLine"]] = relationship(  # noqa: F821
        back_populates="forecast", cascade="all, delete-orphan", lazy="select",
    )
    scenarios: Mapped[list["CashFlowScenario"]] = relationship(  # noqa: F821
        back_populates="forecast", cascade="all, delete-orphan", lazy="select",
    )
    alerts: Mapped[list["CashFlowAlert"]] = relationship(  # noqa: F821
        back_populates="forecast", lazy="select",
    )

    __table_args__ = (
        Index("ix_cf_forecasts_company_stato", "company_id", "stato"),
        Index("ix_cf_forecasts_company_auto", "company_id", "is_auto"),
        Index("ix_cf_forecasts_company_periodo", "company_id", "data_inizio", "data_fine"),
    )
