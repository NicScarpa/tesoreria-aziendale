import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ReminderType


class ScheduleReminder(Base):
    __tablename__ = "schedule_reminders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    schedule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schedules.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    giorni_prima: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    tipo: Mapped[ReminderType] = mapped_column(
        Enum(ReminderType, name="reminder_type",
             create_constraint=True, native_enum=True,
             values_callable=lambda x: [e.value for e in x]),
        nullable=False, default=ReminderType.IN_APP,
    )
    messaggio: Mapped[str | None] = mapped_column(Text, nullable=True)
    inviato: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    data_invio: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    schedule: Mapped["Schedule"] = relationship(back_populates="reminders")  # noqa: F821
