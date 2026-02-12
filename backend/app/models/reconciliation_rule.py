import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import ForeignKey, String, Boolean, Integer, DateTime, Numeric, Enum, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ReconciliationRuleMatchType, ReconciliationRuleAction


class ReconciliationRule(Base):
    __tablename__ = "reconciliation_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    match_amount: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    amount_tolerance: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.01"), nullable=False)
    match_date: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    date_tolerance_days: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    match_description: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    match_counterpart: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    auto_confirm: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    min_confidence: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.80"), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    conditions: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=list)
    match_type: Mapped[ReconciliationRuleMatchType] = mapped_column(
        Enum(ReconciliationRuleMatchType, name="reconciliation_rule_match_type",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=ReconciliationRuleMatchType.EXACT_AMOUNT,
    )
    action: Mapped[ReconciliationRuleAction] = mapped_column(
        Enum(ReconciliationRuleAction, name="reconciliation_rule_action",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=ReconciliationRuleAction.SUGGEST,
    )
    amount_tolerance_override: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    date_tolerance_override: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reference_pattern: Mapped[str | None] = mapped_column(String(255), nullable=True)
    require_same_counterpart: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    times_applied: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    confirmation_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    company: Mapped["Company"] = relationship(back_populates="reconciliation_rules")  # noqa: F821
