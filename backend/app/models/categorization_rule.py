import uuid
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, Boolean, DateTime, Integer, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import FlowDirection, RuleActionType


class CategorizationRule(Base):
    __tablename__ = "categorization_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    direction: Mapped[FlowDirection] = mapped_column(
        Enum(FlowDirection, name="flow_direction", create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    action_type: Mapped[RuleActionType] = mapped_column(
        Enum(RuleActionType, name="rule_action_type", create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=RuleActionType.SET_CATEGORY,
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="CASCADE"), nullable=False
    )
    subcategory_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subcategories.id", ondelete="SET NULL"), nullable=True
    )
    conditions: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    company: Mapped["Company"] = relationship(back_populates="categorization_rules")  # noqa: F821
    category: Mapped["Category"] = relationship(lazy="selectin")  # noqa: F821
    subcategory: Mapped["Subcategory"] = relationship(lazy="selectin")  # noqa: F821
