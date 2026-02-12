import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import WidgetSize, WidgetType


class DashboardWidget(Base):
    __tablename__ = "dashboard_widgets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
    )
    widget_type: Mapped[WidgetType] = mapped_column(
        Enum(WidgetType, name="widget_type",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    posizione: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    colonna: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    dimensione: Mapped[WidgetSize] = mapped_column(
        Enum(WidgetSize, name="widget_size",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=WidgetSize.MEDIUM,
    )
    configurazione: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    visibile: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

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
    user: Mapped["User"] = relationship()  # noqa: F821
    company: Mapped["Company"] = relationship()  # noqa: F821

    __table_args__ = (
        UniqueConstraint("user_id", "company_id", "widget_type", name="uq_dashboard_widget_user_company_type"),
        Index("ix_dashboard_widgets_user_company", "user_id", "company_id"),
    )
