import uuid
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, Boolean, DateTime, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import NotificationType


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"
    __table_args__ = (
        UniqueConstraint("user_id", "company_id", "notification_type", name="uq_notification_pref"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    notification_type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, name="notification_type", create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    in_app: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user: Mapped["User"] = relationship(lazy="selectin")  # noqa: F821
    company: Mapped["Company"] = relationship(back_populates="notification_preferences")  # noqa: F821
