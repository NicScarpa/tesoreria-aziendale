import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint, Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import WebhookType


class WebhookEndpoint(Base):
    __tablename__ = "webhook_endpoints"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    tipo: Mapped[WebhookType] = mapped_column(
        Enum(WebhookType, name="webhook_type",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    url_path: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True,
        default=lambda: str(uuid.uuid4()),
    )
    secret: Mapped[str] = mapped_column(
        String(255), nullable=False,
        default=lambda: uuid.uuid4().hex,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_triggered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    trigger_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failure_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    company: Mapped["Company"] = relationship(back_populates="webhook_endpoints")  # noqa: F821

    __table_args__ = (
        UniqueConstraint("url_path", name="uq_webhook_endpoints_url_path"),
        Index("ix_webhook_endpoints_company_tipo", "company_id", "tipo"),
    )
