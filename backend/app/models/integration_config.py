import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, DateTime, Enum, ForeignKey, String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import IntegrationConnectionStatus, IntegrationType


class IntegrationConfig(Base):
    __tablename__ = "integration_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    integration_type: Mapped[IntegrationType] = mapped_column(
        Enum(IntegrationType, name="integration_type",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    status: Mapped[IntegrationConnectionStatus] = mapped_column(
        Enum(IntegrationConnectionStatus, name="integration_connection_status",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=IntegrationConnectionStatus.NON_CONFIGURATA,
    )
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    encrypted_credentials: Mapped[str | None] = mapped_column(Text, nullable=True)
    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    last_test_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
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

    company: Mapped["Company"] = relationship(back_populates="integration_configs")  # noqa: F821

    __table_args__ = (
        UniqueConstraint("company_id", "integration_type", name="uq_integration_configs_company_type"),
    )
